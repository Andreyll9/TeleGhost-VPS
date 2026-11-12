package core

import (
	"bytes"
	"fmt"
	"image"
	"image/jpeg"
	"image/png"
	"strings"

	_ "image/gif" // Support decoding
)

// StripMetadata removes EXIF and other metadata from an image by decoding and re-encoding it.
// Supported formats: JPEG, PNG.
// Returns the processed image data and the mime type (e.g., "image/jpeg").
// If the format is not supported for re-encoding or an error occurs, returns the original error.
func StripMetadata(data []byte, filename string) ([]byte, string, error) {
	// 1. Decode the image (this ignores metadata usually)
	img, format, err := image.Decode(bytes.NewReader(data))
	if err != nil {
		return nil, "", fmt.Errorf("failed to decode image: %w", err)
	}

	var buf bytes.Buffer
	var mimeType string

	// 2. Re-encode based on format or filename extension
	// We prioritize the detected format, but if it's unknown/generic, check filename.

	switch format {
	case "jpeg":
		mimeType = "image/jpeg"
		// Encode with reasonable quality
		err = jpeg.Encode(&buf, img, &jpeg.Options{Quality: 85})
	case "png":
		mimeType = "image/png"
		err = png.Encode(&buf, img)
	default:
		// Fallback: check extension
		lowerName := strings.ToLower(filename)
		if strings.HasSuffix(lowerName, ".jpg") || strings.HasSuffix(lowerName, ".jpeg") {
			mimeType = "image/jpeg"
			err = jpeg.Encode(&buf, img, &jpeg.Options{Quality: 85})
		} else if strings.HasSuffix(lowerName, ".png") {
			mimeType = "image/png"
			err = png.Encode(&buf, img)
		} else {
			// Unsupported format for stripping, return error or original?
			// Let's return error so caller knows we didn't strip.
			return nil, "", fmt.Errorf("unsupported format for metadata stripping: %s", format)
		}
	}

	if err != nil {
		return nil, "", fmt.Errorf("failed to re-encode image: %w", err)
	}

	return buf.Bytes(), mimeType, nil
}
