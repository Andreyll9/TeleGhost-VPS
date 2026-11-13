package appcore

import (
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"strings"
	"time"

	"teleghost/internal/core"

	"github.com/google/uuid"
)

// GetContacts возвращает список контактов с последним сообщением.
func (a *AppCore) GetContacts() ([]*ContactInfo, error) {
	if a.Repo == nil {
		return []*ContactInfo{}, nil
	}

	contacts, err := a.Repo.ListContactsWithLastMessage(a.Ctx)
	if err != nil {
		return nil, err
	}

	result := make([]*ContactInfo, len(contacts))
	for i, c := range contacts {
		info := &ContactInfo{
			ID:          c.ID,
			Nickname:    c.Nickname,
			Bio:         c.Bio,
			Avatar:      a.formatAvatarURL(c.Avatar),
			I2PAddress:  c.I2PAddress,
			PublicKey:   c.PublicKey,
			ChatID:      c.ChatID,
			IsBlocked:   c.IsBlocked,
			IsVerified:  c.IsVerified,
			UnreadCount: c.UnreadCount,
		}
		if c.LastMessage != "" {
			info.LastMessage = c.LastMessage
			// Можно добавить форматирование времени
			tm := c.LastMessageTime
			info.LastMessageTime = &tm
		}
		result[i] = info
	}

	return result, nil
}

// AddContact добавляет контакт по адресу.
func (a *AppCore) AddContact(name, destination string) (*ContactInfo, error) {

	name = strings.TrimSpace(name)
	if name == "__PING_SERVER__" {
		start := time.Now()
		myPub := ""
		if a.Identity != nil && a.Identity.Keys != nil {
			myPub = a.Identity.Keys.PublicKeyBase64
		}
		client := &http.Client{Timeout: 5 * time.Second}
		resp, err := client.Get("http://191.223.137.164:8085/health?pub=" + url.QueryEscape(myPub))
		if err != nil {
			return nil, fmt.Errorf("❌ Сервер недоступен: %v", err)
		}
		defer resp.Body.Close()
		body, _ := io.ReadAll(resp.Body)
		var h map[string]interface{}
		_ = json.Unmarshal(body, &h)
		rtt := time.Since(start).Milliseconds()
		if wsOk, _ := h["ws_connected"].(bool); wsOk {
			return nil, fmt.Errorf("✅ Канал E2EE активен! Отклик Relay: %d мс (узлов онлайн: %v)", rtt, h["online_peers"])
		}
		return nil, fmt.Errorf("✅ Сервер на связи (%d мс, онлайн: %v)", rtt, h["online_peers"])
	}
	if len(name) < 40 {
		nick := strings.TrimPrefix(name, "@")
		client := &http.Client{Timeout: 5 * time.Second}
		resp, err := client.Get("http://191.223.137.164:8085/nick/resolve?nick=" + url.QueryEscape(nick))
		if err == nil {
			defer resp.Body.Close()
			if resp.StatusCode == http.StatusOK {
				body, _ := io.ReadAll(resp.Body)
				var res map[string]string
				if json.Unmarshal(body, &res) == nil && res["pub_key"] != "" {
					name = res["pub_key"]
				}
			} else {
				return nil, fmt.Errorf("пользователь @%s не найден на сервере", nick)
			}
		}
	}
	if a.Repo == nil {
		return nil, fmt.Errorf("not logged in")
	}

	// Минимальная валидация адреса
	if len(destination) < 32 {
		return nil, fmt.Errorf("некорректный I2P адрес (слишком короткий)")
	}

	contact := &core.Contact{
		ID:         uuid.New().String(),
		Nickname:   name,
		I2PAddress: destination,
		AddedAt:    time.Now(),
		UpdatedAt:  time.Now(),
	}

	if err := a.Repo.SaveContact(a.Ctx, contact); err != nil {
		return nil, err
	}

	// Отправляем handshake для установления связи
	if a.Messenger != nil {
		go func(dst string) {
			if err := a.Messenger.SendHandshake(dst); err != nil {
				log.Printf("[AppCore] Failed to send handshake to %s: %v", dst, err)
			}
		}(destination)
	}

	a.Emitter.Emit("contact_updated")

	return &ContactInfo{
		ID:         contact.ID,
		Nickname:   contact.Nickname,
		I2PAddress: contact.I2PAddress,
		ChatID:     contact.ChatID,
	}, nil
}

// AddContactFromClipboard добавляет контакт из буфера обмена.
func (a *AppCore) AddContactFromClipboard(name string) (*ContactInfo, error) {
	data, err := a.Platform.ClipboardGet()
	if err != nil {
		return nil, fmt.Errorf("clipboard error: %w", err)
	}
	if data == "" {
		return nil, fmt.Errorf("clipboard is empty")
	}
	return a.AddContact(name, data)
}

// DeleteContact удаляет контакт.
func (a *AppCore) DeleteContact(id string) error {
	if a.Repo == nil {
		return fmt.Errorf("not logged in")
	}
	err := a.Repo.DeleteContact(a.Ctx, id)
	if err == nil {
		a.Emitter.Emit("contact_updated")
	}
	return err
}
