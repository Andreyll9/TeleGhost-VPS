// Package main — точка входа приложения TeleGhost
// В production сборке Wails генерирует main.go в корне,
// этот файл предназначен для альтернативной сборки без GUI
package main

import (
	"fmt"
	"os"
)

func main() {
	fmt.Println("TeleGhost CLI Mode")
	fmt.Println("Use 'wails dev' for GUI development")
	fmt.Println("Use 'wails build' for production build")
	os.Exit(0)
}
