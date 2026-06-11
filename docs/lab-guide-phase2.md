# 📥 Phase 2: SOP Ingestion and Indexing

> 📊 **Status:** ████████████████████ 100% Ready | 🏷️ **Version:** 1.0.0 | 📅 **Updated:** 2026-03-09

**⏱ Time Box: ~30 minutes**

## 🎯 Objective

Ingest Standard Operating Procedure (SOP) documents into the platform and create a searchable index. By the end of this phase, your SOPs will be chunked, embedded, and indexed in both Azure AI Search and PostgreSQL (pgvector) — ready for retrieval-augmented generation.

---

## ✅ Prerequisites

- 🔹 Phase 1 complete (all Azure resources provisioned)
- 🔹 Python 3.11+ installed (`python3 --version`)
- 🔹 Project dependencies installed (`pip install -r requirements.txt`)

---

## 📋 Step 1: Upload Sample SOPs to Blob Storage

The repo includes sample SOPs in `evals/datasets/`. Upload them to the `sops` blob container:

```bash
# Set your storage account name
STORAGE_ACCOUNT="staiassistlab"
RESOURCE_GROUP="rg-aiassist-lab"

# Upload sample SOP files
az storage blob upload-batch \
  --account-name $STORAGE_ACCOUNT \
  --destination sops \
  --source evals/datasets/ \
  --auth-mode login \
  --overwrite
```

### ✔️ Verification

```bash
az storage blob list \
  --account-name $STORAGE_ACCOUNT \
  --container-name sops \
  --auth-mode login \
  --query "[].{Name:name, Size:properties.contentLength}" \
  -o table
```

You should see your SOP files listed with non-zero sizes.

> **🗣️ Facilitator Note:** In a production system, SOPs would arrive via a document management pipeline — SharePoint, ServiceNow, or a dedicated upload portal. For this lab, we manually upload to blob storage to focus on the ingestion logic.

---

## 📋 Step 2: Run Ingestion Pipeline

The ingestion pipeline lives in `app/ingestion/`. It reads documents from blob storage, chunks them, and prepares them for embedding.

```bash
# Run the ingestion pipeline
python -m app.ingestion.run \
  --storage-account $STORAGE_ACCOUNT \
  --container sops \
  --output-container processed
```

This pipeline:
1. Downloads documents from the `sops` container
2. Extracts text (supports PDF, DOCX, Markdown, plain text)
3. Splits text into chunks using the configured strategy
4. Writes chunked output to the `processed` container

### ✔️ Verification

```bash
# Check processed chunks in blob storage
az storage blob list \
  --account-name $STORAGE_ACCOUNT \
  --container-name processed \
  --auth-mode login \
  --query "[].name" \
  -o tsv | head -10
```

You should see chunk files (e.g., `sop-001_chunk_0.json`, `sop-001_chunk_1.json`).

---

## 📋 Step 3: Review Chunking Output

Pull down a sample chunk and inspect it:

```bash
# Download and inspect a single chunk
az storage blob download \
  --account-name $STORAGE_ACCOUNT \
  --container-name processed \
  --name "sop-001_chunk_0.json" \
  --auth-mode login \
  --file /tmp/sample_chunk.json

cat /tmp/sample_chunk.json | python -m json.tool
```

Expected structure:

```json
{
  "chunk_id": "sop-001_chunk_0",
  "source_document": "sop-001.md",
  "chunk_index": 0,
  "total_chunks": 12,
  "content": "This SOP covers the procedure for...",
  "metadata": {
    "title": "Incident Response Procedure",
    "category": "security",
    "effective_date": "2024-01-15",
    "token_count": 487
  }
}
```

> **🗣️ Facilitator Note:** Point out the `token_count` field. Each chunk targets ~500 tokens with 50-token overlap. Ask participants: "Why not just send the whole document to the model?" Answer: context window limits, cost, and retrieval precision.

---

## 📋 Step 4: Generate Embeddings

Now we convert each text chunk into a vector embedding using Azure OpenAI's `text-embedding-ada-002` model:

```bash
python -m app.indexing.embed \
  --storage-account $STORAGE_ACCOUNT \
  --container processed \
  --openai-deployment "text-embedding-ada-002"
```

This reads each chunk, calls the embedding API, and attaches the resulting 1536-dimensional vector to the chunk metadata.

### ✔️ Verification

```bash
# Check that embeddings were generated (the chunk file should now include a vector)
az storage blob download \
  --account-name $STORAGE_ACCOUNT \
  --container-name processed \
  --name "sop-001_chunk_0.json" \
  --auth-mode login \
  --file /tmp/sample_embedded.json

# Verify the embedding field exists and has the right dimension
python3 -c "
import json
with open('/tmp/sample_embedded.json') as f:
    chunk = json.load(f)
vec = chunk.get('embedding', [])
print(f'Embedding dimensions: {len(vec)}')
assert len(vec) == 1536, 'Expected 1536 dimensions'
print('✅ Embedding looks correct')
"
```

---

## 📋 Step 5: Index into Azure AI Search

Push the embedded chunks into Azure AI Search:

```bash
python -m app.indexing.search_index \
  --storage-account $STORAGE_ACCOUNT \
  --container processed \
  --search-service "srch-aiassist-lab" \
  --index-name "sops-index"
```

This creates (or updates) a search index with the following fields:
- `chunk_id` (key)
- `content` (searchable text)
- `embedding` (vector field, 1536 dimensions)
- `source_document`, `title`, `category` (filterable metadata)

### ✔️ Verification

```bash
# Check index document count
az search query-key list \
  --resource-group $RESOURCE_GROUP \
  --service-name "srch-aiassist-lab" \
  -o table

# Or use the REST API to check document count
python3 -c "
# Quick index stats check
print('Index created. Verify in Azure Portal:')
print('  → AI Search → srch-aiassist-lab → Indexes → sops-index')
print('  → Check document count matches your chunk count')
"
```

> **🗣️ Facilitator Note:** If the search service isn't ready yet, it can take 1–2 minutes after provisioning. Have participants check the Azure Portal to see the index schema visually.

---

## 📋 Step 6: Store Vectors in PostgreSQL

In parallel with AI Search, we also store embeddings in PostgreSQL using the pgvector extension:

```bash
python -m app.indexing.pg_index \
  --storage-account $STORAGE_ACCOUNT \
  --container processed \
  --pg-host "psql-aiassist-lab.postgres.database.azure.com" \
  --pg-database "aiassist"
```

This:
1. Connects to PostgreSQL using Managed Identity (AAD token)
2. Creates the `sop_chunks` table if it doesn't exist
3. Inserts chunks with their embedding vectors

The table schema:

```sql
CREATE TABLE IF NOT EXISTS sop_chunks (
    chunk_id    TEXT PRIMARY KEY,
    content     TEXT NOT NULL,
    embedding   vector(1536) NOT NULL,
    source_doc  TEXT,
    title       TEXT,
    category    TEXT,
    metadata    JSONB,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Create an IVFFlat index for approximate nearest neighbor search
CREATE INDEX IF NOT EXISTS idx_sop_chunks_embedding
    ON sop_chunks USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);
```

### ✔️ Verification

```bash
# Connect to PostgreSQL and check row count
python3 -c "
# Verify via application connection
print('Verify in PostgreSQL:')
print('  psql -h psql-aiassist-lab.postgres.database.azure.com -U <your-identity> -d aiassist')
print('  SELECT COUNT(*) FROM sop_chunks;')
print('  SELECT chunk_id, LEFT(content, 80) FROM sop_chunks LIMIT 5;')
"
```

---

## 📋 Step 7: Verify Index Contents

Run a quick smoke test to confirm both indexes are populated and working:

```bash
python -m app.indexing.verify \
  --search-service "srch-aiassist-lab" \
  --index-name "sops-index" \
  --pg-host "psql-aiassist-lab.postgres.database.azure.com" \
  --pg-database "aiassist"
```

Expected output:

```
AI Search index 'sops-index':
  Documents: 47
  Fields: chunk_id, content, embedding, source_document, title, category

PostgreSQL 'sop_chunks' table:
  Rows: 47
  Vector dimensions: 1536
  Index type: ivfflat (cosine)

✅ Both indexes are consistent and ready for queries.
```

---

## 💡 Architecture Decision: Chunking Strategy

**Why 500 tokens with 50-token overlap?**

| Chunk Size | Pros | Cons |
|---|---|---|
| 100 tokens | Very precise retrieval | Loses context; more API calls |
| 500 tokens | Good balance of precision and context | May split related paragraphs |
| 1000 tokens | More context per chunk | Retrieval becomes less precise |
| Whole document | Maximum context | Exceeds context window; poor retrieval |

We use **500 tokens** because:
- It fits comfortably within the model's context window alongside the prompt and other chunks
- It's large enough to contain a complete procedure step or policy paragraph
- The **50-token overlap** ensures that sentences split across chunk boundaries are still captured in at least one chunk

In production, you'd tune this based on your document structure. Government SOPs tend to have well-defined sections — consider section-aware chunking as a future improvement.

---

## 💡 Architecture Decision: Embedding Model Choice

We use `text-embedding-ada-002` (1536 dimensions) because:

- 🔹 **Available in Azure Gov** — not all embedding models are available in government regions
- 🔹 **Well-tested** — extensive benchmarks and community knowledge
- 🔹 **Cost-effective** — ~$0.0001 per 1K tokens
- 🔹 **Good enough** — for SOP-style content with clear, structured language, ada-002 performs well

When `text-embedding-3-small` or `text-embedding-3-large` become available in Azure Gov, consider upgrading for better retrieval quality (especially with the dimension reduction feature of the v3 models).

---

> **🗣️ Facilitator Note:** This is a good checkpoint. Ask participants:
> - "How many chunks did your documents produce?"
> - "What happens if you change the chunk size? When would you want to?"
> - "Why do we store vectors in *two* places?"
>
> Emphasize that the dual-index strategy (AI Search + pgvector) is intentional — see ADR-002 in `docs/architecture-decisions.md`.

---

## 🎉 Wrap-Up

At this point, your SOP content is:

- [x] Uploaded to blob storage
- [x] Chunked into ~500-token segments with overlap
- [x] Embedded using `text-embedding-ada-002` (1536 dimensions)
- [x] Indexed in Azure AI Search (hybrid text + vector search)
- [x] Stored in PostgreSQL with pgvector (vector similarity search)
- [x] Verified in both stores

**Next:** [Phase 3 — RAG Query Flow](lab-guide-phase3.md)

---

## 📋 Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-09 | Squad (Beacon 🔦) | Initial release — full lab guide |
