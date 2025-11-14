package main

import (
	"fmt"
	"os"
)

// Config aggregates runtime configuration loaded from environment variables.
type Config struct {
	MaxToken   string
	MaxAPIBase string
	QAHost     string
}

func loadConfig() (Config, error) {
	cfg := Config{
		MaxToken:   os.Getenv("MAX_ACCESS_TOKEN"),
		MaxAPIBase: os.Getenv("MAX_API_BASE"),
		QAHost:     os.Getenv("QA_HOST"),
	}

	if cfg.MaxToken == "" {
		return Config{}, fmt.Errorf("MAX_ACCESS_TOKEN is not set")
	}
	if cfg.MaxAPIBase == "" {
		cfg.MaxAPIBase = "https://platform-api.max.ru"
	}
	if cfg.QAHost == "" {
		cfg.QAHost = "qa:8080"
	}
	return cfg, nil
}
