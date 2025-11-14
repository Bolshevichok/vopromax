package main

import (
	"context"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/joho/godotenv"
	maxbot "github.com/max-messenger/max-bot-api-client-go"
	"github.com/max-messenger/max-bot-api-client-go/schemes"
)

func main() {
	if err := run(); err != nil {
		log.Fatalf("bot stopped: %v", err)
	}
}

func run() error {
	// Load .env for local development, ignore errors if the file does not exist.
	_ = godotenv.Load("../.env")
	_ = godotenv.Load()

	cfg, err := loadConfig()
	if err != nil {
		return err
	}

	api, err := maxbot.New(cfg.MaxToken)
	if err != nil {
		return err
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go func() {
		signals := make(chan os.Signal, 1)
		signal.Notify(signals, syscall.SIGINT, syscall.SIGTERM)
		<-signals
		cancel()
	}()

	log.Printf("Max bot started. QA host=%s", cfg.QAHost)

	for upd := range api.GetUpdates(ctx) {
		handleUpdate(api, upd)
	}

	return ctx.Err()
}

func handleUpdate(api *maxbot.Api, upd interface{}) {
	switch u := upd.(type) {
	case *schemes.MessageCreatedUpdate:
		log.Printf("message from %d: %s", u.Message.Sender.UserId, u.GetText())
	case *schemes.MessageCallbackUpdate:
		log.Printf("callback from %d payload=%s", u.Callback.User.UserId, u.Callback.Payload)
	default:
		log.Printf("update: %#v", u)
	}
}
