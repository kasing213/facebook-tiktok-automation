#!/bin/bash
# scripts/start_ngrok.sh
# Bash script to start ngrok tunnel for webhook development

PORT=8000
REGION="us"

# Show help
show_help() {
    echo -e "\033[1;36mNgrok Tunnel Starter for Facebook/TikTok Webhooks\033[0m"
    echo ""
    echo -e "\033[1;33mUsage: ./start_ngrok.sh [-p <port>] [-r <region>] [-h]\033[0m"
    echo ""
    echo "Options:"
    echo "  -p, --port      Port to expose (default: 8000)"
    echo "  -r, --region    ngrok region (us, eu, ap, au, sa, jp, in - default: us)"
    echo "  -h, --help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  ./start_ngrok.sh                    # Start with defaults"
    echo "  ./start_ngrok.sh -p 3000            # Expose port 3000"
    echo "  ./start_ngrok.sh -r eu              # Use EU region"
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            ;;
    esac
done

# Check if ngrok is installed
echo -e "\033[1;36mChecking for ngrok...\033[0m"
if ! command -v ngrok &> /dev/null; then
    echo -e "\033[1;31mERROR: ngrok is not installed!\033[0m"
    echo ""
    echo -e "\033[1;33mPlease install ngrok:\033[0m"
    echo "  1. Download from: https://ngrok.com/download"
    echo "  2. Or install with brew: brew install ngrok"
    echo "  3. Or install with snap: snap install ngrok"
    echo ""
    exit 1
fi

echo -e "\033[1;32m✓ ngrok found at: $(which ngrok)\033[0m"

# Check if port is in use
echo -e "\033[1;36mChecking if port $PORT is in use...\033[0m"
if ! lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo -e "\033[1;33mWARNING: Port $PORT is not in use. Make sure your app is running!\033[0m"
    echo -e "\033[1;33mStart your app first with: uvicorn app.main:app --reload --port $PORT\033[0m"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo ""
echo -e "\033[1;36m================================================\033[0m"
echo -e "\033[1;36m Starting ngrok tunnel for webhooks...\033[0m"
echo -e "\033[1;36m================================================\033[0m"
echo ""
echo -e "Port:   \033[1;37m$PORT\033[0m"
echo -e "Region: \033[1;37m$REGION\033[0m"
echo ""
echo -e "\033[1;33mPress Ctrl+C to stop the tunnel\033[0m"
echo ""
echo -e "\033[1;32mWeb Interface: http://localhost:4040\033[0m"
echo ""

# Start ngrok
ngrok http $PORT --region=$REGION
