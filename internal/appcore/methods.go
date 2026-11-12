package appcore

// SetActiveChat sets the active chat ID thread-safely
func (a *AppCore) SetActiveChat(chatID string) {
	a.mu.Lock()
	defer a.mu.Unlock()
	a.ActiveChatID = chatID
}

// GetActiveChatID gets the active chat ID thread-safely
func (a *AppCore) GetActiveChatID() string {
	a.mu.RLock()
	defer a.mu.RUnlock()
	return a.ActiveChatID
}
