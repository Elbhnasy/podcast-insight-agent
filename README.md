# 🎙️ Podcast Insight Agent

An AI-powered agent for discovering, analyzing, and generating insights from AI-related podcasts. This system automatically transcribes recent podcast content, extracts key insights, and makes this knowledge accessible through both email summaries and a conversational search interface.

![License](https://img.shields.io/badge/license-MIT-blue)
![Python](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11-blue)

## 🌟 Features

- **Automatic Podcast Discovery**: Finds the latest AI-related podcasts from popular channels
- **Transcript Generation**: Creates complete transcripts of podcast episodes
- **Intelligent Summarization**: Extracts key insights, technical details, and resource mentions
- **Vector Search**: Enables semantic search across podcast content
- **Conversational Interface**: Ask questions about podcast content in natural language
- **Structured Storage**: Organizes insights in MongoDB for persistence
- **Email Reports**: Delivers formatted summaries via email

## 🏗️ Architecture

The system consists of several key components:

1. **Summarizer Agent**: LLM-powered agent that discovers and analyzes podcasts
2. **Vector Store**: Pinecone-based semantic search for podcast insights
3. **Retrieval System**: RAG implementation for answering queries about podcast content
4. **API Server**: Flask-based REST API for integration with frontend applications
5. **Database**: MongoDB for structured storage of podcast summaries

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- MongoDB
- Pinecone account
- OpenAI API key
- Google API credentials (for email functionality)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Elbhnasy/podcast-insight-agent.git
   cd podcast-insight-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

### Running the Application

#### Generate Podcast Insights

```bash
python main.py query --message "Find and summarize the latest AI podcasts"
```

#### Sync to Vector Database

```bash
python main.py sync --limit 5
```

#### Start the API Server

```bash
python -m src.api.server
```

## 🐳 Docker Deployment

Build and run using Docker:

```bash
docker build -t podcast-insight-agent -f src/Dockerfile .
docker run -p 8000:8000 --env-file .env podcast-insight-agent
```

## 📊 Project Structure

```
podcast-insight-agent/
├── src/
│   ├── agent/              # LLM-powered agent for podcast analysis
│   ├── api/                # Flask API server
│   ├── prompts/            # System prompts and templates
│   ├── retriever/          # RAG implementation for Q&A
│   ├── utils/              # Utility functions and tools
│   ├── vectorstore/        # Vector database integration
│   └── Dockerfile          # Docker configuration
├── main.py                 # CLI entry point
├── requirements.txt        # Project dependencies
└── README.md               # Project documentation
```

## 🔧 Configuration

The application uses environment variables for configuration:

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | None |
| `PINECONE_API_KEY` | Pinecone API key | None |
| `PINECONE_INDEX_NAME` | Pinecone index name | podcast-summaries |
| `MONGODB_URI` | MongoDB connection string | None |
| `GOOGLE_CLIENT_ID` | Google API client ID | None |
| `GOOGLE_CLIENT_SECRET` | Google API client secret | None |
| `EMAIL_RECIPIENT` | Email recipient address | None |

## 📚 Usage Examples

### Finding Insights on Specific Topics

```bash
python main.py query --message "Find insights about transformer architecture alternatives from recent podcasts"
```

### API Interaction

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What are the latest developments in AI alignment?"}'
```

## 📝 API Documentation

The API provides the following endpoints:

- `POST /api/v1/chat`: Submit a query about podcast content
- `GET /api/v1/health`: Check API health status

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgements

- [LangChain](https://github.com/langchain-ai/langchain) - LLM application framework
- [Pinecone](https://www.pinecone.io/) - Vector database
- [OpenAI](https://openai.com/) - LLM and embedding models
- [MongoDB](https://www.mongodb.com/) - Document database
- [Flask](https://flask.palletsprojects.com/) - Web framework
