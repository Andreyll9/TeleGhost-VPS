package appcore

import (
	"encoding/json"
	"log"
	"os"
	"path/filepath"
)

// GetMyDestination возвращает крипто-ключ Hydra.
func (a *AppCore) GetMyDestination() string {
	if a.Messenger == nil {
		if a.Identity != nil && a.Identity.Keys != nil {
			return a.Identity.Keys.PublicKeyBase64
		}
		return ""
	}
	return a.Messenger.GetDestination()
}

// GetRouterSettings возвращает настройки соединения.
func (a *AppCore) GetRouterSettings() *RouterSettings {
	settingsFile := filepath.Join(a.DataDir, "router_settings.json")

	defaultSettings := &RouterSettings{
		TunnelLength: 1,
		LogToFile:    false,
	}

	data, err := os.ReadFile(settingsFile)
	if err != nil {
		return defaultSettings
	}

	var settings RouterSettings
	if err := json.Unmarshal(data, &settings); err != nil {
		log.Printf("[AppCore] Failed to parse router settings: %v", err)
		return defaultSettings
	}

	return &settings
}

// GetAppAboutInfo возвращает информацию о приложении Hydra.
func (a *AppCore) GetAppAboutInfo() *AppAboutInfo {
	return &AppAboutInfo{
		AppVersion: "2.0.0-hydra",
		I2PVersion: "Hydra Relay v2 (X25519 + XChaCha20)",
		I2PPath:    "Локальная зашифрованная БД (SQLite E2EE)",
		Author:     "Andreyll9 (Hydra) | Core: TeleGhost (MIT)",
		License:    "MIT / Open Source",
	}
}

// SaveRouterSettings сохраняет настройки роутера.
func (a *AppCore) SaveRouterSettings(settings map[string]interface{}) error {
	settingsFile := filepath.Join(a.DataDir, "router_settings.json")

	current := a.GetRouterSettings()

	if val, ok := settings["tunnelLength"].(float64); ok {
		current.TunnelLength = int(val)
	}
	if val, ok := settings["logToFile"].(bool); ok {
		current.LogToFile = val
	}

	data, err := json.MarshalIndent(current, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(settingsFile, data, 0600)
}

// GetNetworkStatus возвращает текущий статус сети
func (a *AppCore) GetNetworkStatus() string {
	return string(a.Status)
}
