# Valmiki Ramayanam — MCP Server

A self-hosted [Model Context Protocol](https://modelcontextprotocol.io/) server that gives Claude deep, searchable access to all seven kandas of the Valmiki Ramayanam — complete with knowledge-graph retrieval, semantic search, and authentic Sanskrit verse citations.

```
┌─────────────────┐       ┌──────────────────────────────────────────────┐
│  Claude Desktop  │       │            Docker Container                 │
│                  │  MCP  │  ┌────────────┐    ┌─────────────────────┐  │
│  "Who is the    ├───────►  │  FastMCP    ├───►│  RAG + KG Engine    │  │
│   father of     │◄───────┤  │  Server     │◄───┤  (7 Kanda Indices)  │  │
│   Dasharatha?"  │       │  └────────────┘    └─────────────────────┘  │
└─────────────────┘       └──────────────────────────────────────────────┘
```

---

## What You Get

Three tools available directly inside Claude Desktop:

| Tool | Purpose |
|------|---------|
| `get_ramayana_context` | Search across **all 7 kandas** — the primary entry point for any question |
| `get_kanda_context` | Deep-dive into a **specific kanda** when the broad search needs refinement |
| `get_original_verses` | Retrieve **authentic Sanskrit verses** with translations for any referenced chunk |

Every response includes chunk IDs (e.g. `1_12_3` = Balakanda, Chapter 12, Chunk 3) that trace back to the original text.

---

## Prerequisites

| Requirement | Version | Install |
|-------------|---------|---------|
| **Docker** (with Compose) | 20.10+ | [docs.docker.com/get-docker](https://docs.docker.com/get-docker/) |
| **Node.js** | 18+ | [nodejs.org](https://nodejs.org/) |
| **Claude Desktop** | Latest | [claude.ai/download](https://claude.ai/download) |

> **Node.js** is needed for `npx mcp-remote`, which bridges Claude Desktop's stdio transport to the server's HTTP transport.

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/Narasimha-3/Ramayanam.git
cd Ramayanam
```

### 2. Start the server

```bash
docker compose up -d --build
```

The first build takes a few minutes — it downloads PyTorch (CPU), the embedding model, and NLTK data. Subsequent starts are near-instant.

Verify it's running:

```bash
docker compose ps
```

You should see the `ramayana` service with status **Up** and port `8090->8000`.

### 3. Configure Claude Desktop

Open the Claude Desktop configuration file for your operating system:

<table>
<tr><th>Operating System</th><th>Config File Location</th></tr>
<tr>
<td><strong>macOS</strong></td>
<td>

```
~/Library/Application Support/Claude/claude_desktop_config.json
```

</td>
</tr>
<tr>
<td><strong>Windows</strong></td>
<td>

```
%APPDATA%\Claude\claude_desktop_config.json
```

</td>
</tr>
<tr>
<td><strong>Linux</strong></td>
<td>

```
~/.config/Claude/claude_desktop_config.json
```

</td>
</tr>
</table>

Add the following to the `mcpServers` section. If the file already has other MCP servers configured, merge this entry into the existing `mcpServers` object.

#### macOS / Linux

```json
{
  "mcpServers": {
    "valmiki-ramayanam": {
      "command": "npx",
      "args": ["-y", "mcp-remote", "http://localhost:8090/mcp"]
    }
  }
}
```

> **Note:** If `npx` is not on the default shell PATH (common with version managers like `nvm`), use the full path instead:
>
> ```json
> "command": "/full/path/to/npx"
> ```
>
> Find it by running `which npx` in your terminal.

#### Windows

On Windows, Claude Desktop cannot invoke `npx` directly — it must be called through `cmd.exe`. Additionally, use `127.0.0.1` instead of `localhost` to avoid IPv6 resolution issues with Docker Desktop.

```json
{
  "mcpServers": {
    "valmiki-ramayanam": {
      "command": "C:\\WINDOWS\\System32\\cmd.exe",
      "args": ["/C", "C:\\Program Files\\nodejs\\npx.cmd", "-y", "mcp-remote", "http://127.0.0.1:8090/mcp"]
    }
  }
}
```

> **Note:** If Node.js is installed in a different location, adjust the path to `npx.cmd` accordingly. Find it by running `where npx` in Command Prompt.

### 4. Restart Claude Desktop

Quit and reopen Claude Desktop. The **Valmiki Ramayanam** server should appear in the MCP tools list with three tools available.

---

## Verify Everything Works

### From the terminal

```bash
curl -X POST http://localhost:8090/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{
    "jsonrpc": "2.0",
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",
      "capabilities": {},
      "clientInfo": {"name": "test", "version": "0.1"}
    },
    "id": 1
  }'
```

A successful response looks like:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "serverInfo": {
      "name": "Valmiki Ramayanam",
      "version": "1.27.1"
    }
  }
}
```

### From Claude Desktop

Ask Claude a question like:

> *"Who is the father of Dasharatha according to Valmiki Ramayanam?"*

Claude should call `get_ramayana_context`, retrieve relevant passages, and cite specific chunk IDs tracing back to the original text.

---

## Architecture

```
Claude Desktop
    │
    │  stdio
    ▼
mcp-remote (npx)
    │
    │  HTTP (Streamable HTTP transport)
    ▼
┌─────────────────────────── Docker ───────────────────────────┐
│                                                              │
│   FastMCP Server (:8000)                                     │
│       │                                                      │
│       ├── get_ramayana_context ──┐                           │
│       ├── get_kanda_context ─────┤                           │
│       └── get_original_verses ───┘                           │
│                                  │                           │
│                                  ▼                           │
│                        Ramayana Engine                       │
│                 ┌──────────┬───────────┐                     │
│                 │          │           │                      │
│              General    7 Kanda     Verse                    │
│             RAG Index   KG Engines  Lookup                   │
│                 │          │           │                      │
│                 ▼          ▼           ▼                      │
│           ramayana_    KGs/        chunks/                   │
│           512_index/   (per kanda) (verse JSONs)             │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Retrieval strategy:**
- **Hybrid search** — combines embedding similarity (BGE-small) with BM25 text matching
- **Knowledge graphs** — one per kanda, storing entity relationships as triplets
- **Reranking** — cosine similarity reranking of KG triplets against the query
- **No LLM in the loop** — the engine uses a keyword extractor (not a generative model), so all returned text is authentic Valmiki Ramayanam content

---

## The Seven Kandas

| # | Kanda | Contents |
|---|-------|----------|
| 1 | **Balakanda** | Birth of Rama, his education, marriage to Sita |
| 2 | **Ayodhyakanda** | Exile of Rama, Dasharatha's grief and death |
| 3 | **Aranyakanda** | Life in the forest, abduction of Sita |
| 4 | **Kishkindhakanda** | Alliance with Sugriva, search for Sita |
| 5 | **Sundarakanda** | Hanuman's journey to Lanka, finding Sita |
| 6 | **Yuddhakanda** | The great war, defeat of Ravana |
| 7 | **Uttarakanda** | Rama's reign, the final departure |

---

## Data

All data is included in this repository and baked into the Docker image at build time — no volume mounts needed:

| Directory | Size | Contents |
|-----------|------|----------|
| `KGs/` | ~242 MB | Knowledge graph indices for each kanda (triplets, embeddings, document stores) |
| `chunks/` | ~35 MB | Chunked and indexed verse text with chapter summaries |
| `ramayana_512_index/` | ~26 MB | General RAG index across the entire Ramayanam |

---

## Managing the Server

```bash
# Start
docker compose up -d

# Stop
docker compose down

# View logs
docker compose logs -f

# Rebuild after code changes
docker compose up -d --build
```

---

## Troubleshooting

**Container starts but Claude Desktop can't connect**
- Verify the container is running: `docker compose ps`
- Verify port 8090 is accessible: `curl http://localhost:8090/mcp`
- Ensure no other service is using port 8090
- Check that `npx` is accessible from the default shell PATH

**Claude Desktop shows the server but tools don't appear**
- Check container logs for startup errors: `docker compose logs`
- The engine loads all 7 KG indices at startup — this takes ~30 seconds

**`npx` not found by Claude Desktop**
- Claude Desktop spawns processes without your shell profile, so `nvm`-managed Node.js may not be on PATH
- **macOS/Linux:** Use the full path to `npx` in the config (run `which npx` to find it)
- **Windows:** `npx` must be called through `cmd.exe` — see the Windows config example above

**Connection fails with `ECONNREFUSED` or `SocketError: other side closed` (Windows)**
- Make sure Docker Desktop is running and the container is up: `docker compose ps`
- Use `http://127.0.0.1:8090/mcp` instead of `http://localhost:8090/mcp` — on Windows, `localhost` often resolves to `::1` (IPv6) while Docker Desktop listens on IPv4 only

**Port conflict on 8090**
- Change the host port in `docker-compose.yml`: `"9090:8000"`
- Update the Claude Desktop config URL accordingly: `http://127.0.0.1:9090/mcp`

---

## License

This project provides tooling for accessing the public-domain text of Valmiki's Ramayanam.
