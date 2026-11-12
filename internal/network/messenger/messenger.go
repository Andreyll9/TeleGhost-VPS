package messenger

import (
	"context"
	"fmt"
	"log"
	"net/url"
	"sync"
	"time"

	"teleghost/internal/core"
	"teleghost/internal/core/identity"
	"teleghost/internal/network/router"
	pb "teleghost/internal/proto"

	"github.com/gorilla/websocket"
	"google.golang.org/protobuf/proto"
)

const RelayServerURL = "ws://191.223.137.164:8085/ws"

const (
	ProtocolVersion   = 1
	MaxPacketSize     = 50 * 1024 * 1024
	HeartbeatInterval = 30 * time.Second
)

type Envelope struct {
	To      string `json:"to"`
	From    string `json:"from"`
	Payload []byte `json:"payload"`
}

type FileOfferHandler func(senderPubKey, messageID, chatID string, filenames []string, totalSize int64, fileCount int32)
type FileResponseHandler func(senderPubKey, messageID, chatID string, accepted bool)
type MessageHandler func(msg *core.Message, senderPubKey, senderAddr string)
type ContactRequestHandler func(senderPubKey, nickname, i2pAddress string)
type ProfileUpdateHandler func(senderPubKey, nickname, bio string, avatar []byte, senderAddr string)
type ProfileRequestHandler func(requestorPubKey string)
type AttachmentSaver func(filename string, data []byte) (string, error)

type Service struct {
	identity              *identity.Keys
	handler               MessageHandler
	contactHandler        ContactRequestHandler
	profileHandler        ProfileUpdateHandler
	profileRequestHandler ProfileRequestHandler
	fileOfferHandler      FileOfferHandler
	fileResponseHandler   FileResponseHandler
	attachmentSaver       AttachmentSaver

	wsConn     *websocket.Conn
	writeMu    sync.Mutex
	ctx        context.Context
	cancel     context.CancelFunc
	wg         sync.WaitGroup
	started    bool
	mu         sync.Mutex
	myNickname string
}

func NewService(_ *router.SAMRouter, id *identity.Keys, handler MessageHandler) *Service {
	return &Service{
		identity:   id,
		handler:    handler,
		myNickname: "User",
	}
}

func (s *Service) SetContactHandler(h ContactRequestHandler)        { s.contactHandler = h }
func (s *Service) SetNickname(nickname string)                      { s.myNickname = nickname }
func (s *Service) SetAttachmentSaver(saver AttachmentSaver)         { s.attachmentSaver = saver }
func (s *Service) SetProfileUpdateHandler(h ProfileUpdateHandler)   { s.profileHandler = h }
func (s *Service) SetFileOfferHandler(h FileOfferHandler)           { s.fileOfferHandler = h }
func (s *Service) SetFileResponseHandler(h FileResponseHandler)     { s.fileResponseHandler = h }
func (s *Service) SetProfileRequestHandler(h ProfileRequestHandler) { s.profileRequestHandler = h }

func (s *Service) GetDestination() string {
	return s.identity.PublicKeyBase64
}

func (s *Service) Start(ctx context.Context) error {
	s.mu.Lock()
	if s.started {
		s.mu.Unlock()
		return fmt.Errorf("service already started")
	}
	s.started = true
	s.ctx, s.cancel = context.WithCancel(ctx)
	s.mu.Unlock()

	if err := s.connectWS(); err != nil {
		log.Printf("[Messenger] Ожидание подключения к VPS: %v", err)
	}

	s.wg.Add(1)
	go s.readLoop()

	s.wg.Add(1)
	go s.heartbeatLoop()

	return nil
}

func (s *Service) connectWS() error {
	u, err := url.Parse(RelayServerURL)
	if err != nil {
		return err
	}
	q := u.Query()
	q.Set("addr", s.GetDestination())
	u.RawQuery = q.Encode()

	dialer := websocket.Dialer{HandshakeTimeout: 10 * time.Second}
	conn, _, err := dialer.DialContext(s.ctx, u.String(), nil)
	if err != nil {
		return err
	}
	conn.SetReadLimit(MaxPacketSize + 1024*1024)

	s.writeMu.Lock()
	if s.wsConn != nil {
		_ = s.wsConn.Close()
	}
	s.wsConn = conn
	s.writeMu.Unlock()
	return nil
}

func (s *Service) Stop() error {
	s.mu.Lock()
	if !s.started {
		s.mu.Unlock()
		return nil
	}
	s.started = false
	s.mu.Unlock()

	if s.cancel != nil {
		s.cancel()
	}

	s.writeMu.Lock()
	if s.wsConn != nil {
		_ = s.wsConn.Close()
		s.wsConn = nil
	}
	s.writeMu.Unlock()

	s.wg.Wait()
	return nil
}

func (s *Service) SendMessage(destination string, packet *pb.Packet) error {
	packet.Version = ProtocolVersion
	packet.SenderPubKey = []byte(s.identity.PublicKeyBase64)

	if len(packet.Payload) > 0 {
		packet.Signature = s.identity.SignMessage(packet.Payload)
	}

	data, err := proto.Marshal(packet)
	if err != nil {
		return err
	}

	env := Envelope{
		To:      destination,
		From:    s.GetDestination(),
		Payload: data,
	}

	s.writeMu.Lock()
	conn := s.wsConn
	if conn == nil {
		s.writeMu.Unlock()
		if err := s.connectWS(); err != nil {
			return err
		}
		s.writeMu.Lock()
		conn = s.wsConn
	}
	defer s.writeMu.Unlock()

	_ = conn.SetWriteDeadline(time.Now().Add(30 * time.Second))
	if err := conn.WriteJSON(env); err != nil {
		_ = conn.Close()
		s.wsConn = nil
		return err
	}
	return nil
}

func (s *Service) readLoop() {
	defer s.wg.Done()
	for {
		select {
		case <-s.ctx.Done():
			return
		default:
		}

		s.writeMu.Lock()
		conn := s.wsConn
		s.writeMu.Unlock()

		if conn == nil {
			if err := s.connectWS(); err != nil {
				select {
				case <-s.ctx.Done():
					return
				case <-time.After(3 * time.Second):
					continue
				}
			}
			continue
		}

		var env Envelope
		if err := conn.ReadJSON(&env); err != nil {
			s.writeMu.Lock()
			if s.wsConn == conn {
				_ = s.wsConn.Close()
				s.wsConn = nil
			}
			s.writeMu.Unlock()
			time.Sleep(2 * time.Second)
			continue
		}

		packet := &pb.Packet{}
		if err := proto.Unmarshal(env.Payload, packet); err != nil {
			continue
		}
		s.handlePacket(packet, env.From)
	}
}

func (s *Service) heartbeatLoop() {
	defer s.wg.Done()
	ticker := time.NewTicker(HeartbeatInterval)
	defer ticker.Stop()

	for {
		select {
		case <-s.ctx.Done():
			return
		case <-ticker.C:
			s.writeMu.Lock()
			if s.wsConn != nil {
				_ = s.wsConn.WriteControl(websocket.PingMessage, []byte{}, time.Now().Add(5*time.Second))
			}
			s.writeMu.Unlock()
		}
	}
}

func (s *Service) SendTextMessageWithID(destination, chatID, messageID, content, replyToID string) error {
	payload, err := proto.Marshal(&pb.TextMessage{
		ChatId:    chatID,
		Content:   content,
		Timestamp: time.Now().UnixMilli(),
		MessageId: messageID,
		ReplyToId: replyToID,
	})
	if err != nil {
		return err
	}
	return s.SendMessage(destination, &pb.Packet{Type: pb.PacketType_TEXT_MESSAGE, Payload: payload})
}

func (s *Service) SendAttachmentMessage(destination, chatID, content string, attachments []*pb.Attachment) error {
	msgID := fmt.Sprintf("%d-%s", time.Now().UnixMilli(), s.identity.UserID[:8])
	return s.SendAttachmentMessageWithID(destination, chatID, msgID, content, "", attachments)
}

func (s *Service) SendAttachmentMessageWithID(destination, chatID, messageID, content, replyToID string, attachments []*pb.Attachment) error {
	payload, err := proto.Marshal(&pb.TextMessage{
		ChatId:      chatID,
		Content:     content,
		Timestamp:   time.Now().UnixMilli(),
		MessageId:   messageID,
		Attachments: attachments,
		ReplyToId:   replyToID,
	})
	if err != nil {
		return err
	}
	return s.SendMessage(destination, &pb.Packet{Type: pb.PacketType_TEXT_MESSAGE, Payload: payload})
}

func (s *Service) SendFileOffer(destination, chatID, messageID string, filenames []string, totalSize int64, fileCount int32) error {
	payload, err := proto.Marshal(&pb.FileOffer{
		MessageId: messageID,
		ChatId:    chatID,
		Filenames: filenames,
		TotalSize: totalSize,
		FileCount: fileCount,
	})
	if err != nil {
		return err
	}
	return s.SendMessage(destination, &pb.Packet{Type: pb.PacketType_FILE_OFFER, Payload: payload})
}

func (s *Service) SendFileResponse(destination, chatID, messageID string, accepted bool) error {
	payload, err := proto.Marshal(&pb.FileResponse{
		MessageId: messageID,
		ChatId:    chatID,
		Accepted:  accepted,
	})
	if err != nil {
		return err
	}
	return s.SendMessage(destination, &pb.Packet{Type: pb.PacketType_FILE_RESPONSE, Payload: payload})
}

func (s *Service) SendHandshake(destination string) error {
	payload, err := proto.Marshal(&pb.Handshake{
		InitiatorPubKey: []byte(s.identity.PublicKeyBase64),
		Timestamp:       time.Now().UnixMilli(),
		Nickname:        s.myNickname,
		I2PAddress:      s.GetDestination(),
	})
	if err != nil {
		return err
	}
	return s.SendMessage(destination, &pb.Packet{Type: pb.PacketType_HANDSHAKE, Payload: payload})
}

func (s *Service) SendProfileRequest(destination string) error {
	return s.SendMessage(destination, &pb.Packet{Type: pb.PacketType_PROFILE_REQUEST, Payload: []byte{}})
}

func (s *Service) SendProfileUpdate(destination, nickname, bio string, avatar []byte) error {
	payload, err := proto.Marshal(&pb.ProfileUpdate{
		Nickname: nickname,
		Bio:      bio,
		Avatar:   avatar,
	})
	if err != nil {
		return err
	}
	return s.SendMessage(destination, &pb.Packet{Type: pb.PacketType_PROFILE_UPDATE, Payload: payload})
}

func (s *Service) handlePacket(packet *pb.Packet, remoteAddr string) {
	senderPubKey := string(packet.SenderPubKey)
	if len(packet.Payload) > 0 && len(packet.Signature) > 0 {
		if valid, err := identity.VerifySignatureBase64(senderPubKey, packet.Payload, packet.Signature); err != nil || !valid {
			return
		}
	}

	switch packet.Type {
	case pb.PacketType_TEXT_MESSAGE:
		s.handleTextMessage(packet, senderPubKey, remoteAddr)
	case pb.PacketType_PROFILE_UPDATE:
		p := &pb.ProfileUpdate{}
		if proto.Unmarshal(packet.Payload, p) == nil && s.profileHandler != nil {
			s.profileHandler(senderPubKey, p.Nickname, p.Bio, p.Avatar, remoteAddr)
		}
	case pb.PacketType_HANDSHAKE:
		h := &pb.Handshake{}
		if proto.Unmarshal(packet.Payload, h) == nil && s.contactHandler != nil {
			nick := h.Nickname
			if nick == "" {
				nick = "Unknown"
			}
			s.contactHandler(senderPubKey, nick, h.I2PAddress)
		}
	case pb.PacketType_PROFILE_REQUEST:
		if s.profileRequestHandler != nil {
			s.profileRequestHandler(senderPubKey)
		}
	case pb.PacketType_FILE_OFFER:
		o := &pb.FileOffer{}
		if proto.Unmarshal(packet.Payload, o) == nil && s.fileOfferHandler != nil {
			s.fileOfferHandler(senderPubKey, o.MessageId, o.ChatId, o.Filenames, o.TotalSize, o.FileCount)
		}
	case pb.PacketType_FILE_RESPONSE:
		r := &pb.FileResponse{}
		if proto.Unmarshal(packet.Payload, r) == nil && s.fileResponseHandler != nil {
			s.fileResponseHandler(senderPubKey, r.MessageId, r.ChatId, r.Accepted)
		}
	}
}

func (s *Service) handleTextMessage(packet *pb.Packet, senderPubKey, remoteAddr string) {
	textMsg := &pb.TextMessage{}
	if err := proto.Unmarshal(packet.Payload, textMsg); err != nil || len(textMsg.Content) > 4096 {
		return
	}

	msg := &core.Message{
		ID:          textMsg.MessageId,
		ChatID:      textMsg.ChatId,
		SenderID:    senderPubKey,
		Content:     textMsg.Content,
		ContentType: "text",
		Status:      core.MessageStatusDelivered,
		IsOutgoing:  false,
		Timestamp:   textMsg.Timestamp,
		CreatedAt:   time.Now(),
		UpdatedAt:   time.Now(),
	}
	if textMsg.ReplyToId != "" {
		msg.ReplyToID = &textMsg.ReplyToId
	}

	if len(textMsg.Attachments) > 0 {
		msg.ContentType = "mixed"
		for _, att := range textMsg.Attachments {
			path := ""
			if s.attachmentSaver != nil {
				if savedPath, err := s.attachmentSaver(att.Filename, att.Data); err == nil {
					path = savedPath
				}
			}
			msg.Attachments = append(msg.Attachments, &core.Attachment{
				ID:           att.Id,
				MessageID:    msg.ID,
				Filename:     att.Filename,
				MimeType:     att.MimeType,
				Size:         att.Size,
				LocalPath:    path,
				IsCompressed: att.IsCompressed,
				Width:        int(att.Width),
				Height:       int(att.Height),
			})
		}
	}

	if s.handler != nil {
		s.handler(msg, senderPubKey, remoteAddr)
	}
}
