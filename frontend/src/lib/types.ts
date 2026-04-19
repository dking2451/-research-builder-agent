export type UUID = string;

export type Project = {
  id: UUID;
  user_id: UUID;
  title: string;
  description: string | null;
  goal: string | null;
  mode_default: string | null;
  status: string;
  tags: string[] | null;
  created_at: string;
  updated_at: string;
};

export type VerificationStatus = "unverified" | "partially_verified" | "verified" | "disputed";
export type EvidenceStrength = "weak" | "medium" | "strong";

export type KnowledgeItem = {
  id: UUID;
  project_id: UUID;
  type: string;
  title: string;
  content: string;
  source_name: string | null;
  source_url: string | null;
  confidence: number | null;
  importance_score: number | null;
  is_pinned: boolean;
  is_archived: boolean;
  verification_status: VerificationStatus;
  evidence_strength: EvidenceStrength;
  tags: string[] | null;
  metadata_json: Record<string, unknown> | null;
  created_by: string;
  embedding_ref: string | null;
  created_at: string;
  updated_at: string;
};

export type SourceCitation = {
  source_record_id: UUID;
  title: string;
  url: string | null;
  source_type: string | null;
  citation_note: string | null;
  locator: string | null;
};

export type SourceRecordSummary = {
  id: UUID;
  title: string;
  url: string | null;
  source_type: string | null;
};

export type RelatedKnowledgeRef = {
  knowledge_id: UUID;
  title: string;
  direction: "outgoing" | "incoming";
  relation_type: string | null;
};

export type KnowledgeDetail = KnowledgeItem & {
  related: RelatedKnowledgeRef[];
  linked_sources: SourceCitation[];
};

export type ProjectDigest = {
  project_id: UUID;
  pinned_knowledge: KnowledgeItem[];
  latest_findings: KnowledgeItem[];
  latest_artifacts: Artifact[];
  next_tasks: TaskItem[];
};

export type Artifact = {
  id: UUID;
  project_id: UUID;
  artifact_type: string;
  title: string;
  content: string;
  format: string;
  is_pinned?: boolean;
  importance_score?: number | null;
  created_at: string;
  updated_at: string;
};

export type Conversation = {
  id: UUID;
  project_id: UUID;
  title: string | null;
  created_at: string;
  updated_at: string;
};

export type Message = {
  id: UUID;
  conversation_id: UUID;
  role: string;
  content: string;
  created_at: string;
};

export type ConversationDetail = Conversation & { messages: Message[] };

export type AgentMode = "research" | "decide" | "build" | "learn";

export type SelectedContextDebug = {
  mode: AgentMode;
  project_summary: {
    project_id: UUID;
    title: string;
    goal: string | null;
    description_excerpt: string | null;
  };
  knowledge_items: Array<{
    id: UUID;
    type: string;
    title: string;
    content_excerpt: string;
    is_pinned: boolean;
    importance_score: number | null;
    role: "pinned" | "finding" | "conclusion" | "related" | "supplemental";
    selection_reason: string;
  }>;
  tasks: Array<{ id: UUID; title: string; status: string; priority: number }>;
  artifacts: Array<{ id: UUID; artifact_type: string; title: string; content_excerpt: string }>;
  context_notes: string[];
  caps: Record<string, unknown>;
};

export type AgentRunResponse = {
  assistant_message_id: UUID;
  display_markdown: string;
  structured: Record<string, unknown>;
  saved_knowledge: KnowledgeItem[];
  saved_artifacts: Artifact[];
  saved_tasks: TaskItem[];
  saved_source_ids: UUID[];
  selected_context: SelectedContextDebug;
};

export type TaskItem = {
  id: UUID;
  project_id: UUID;
  title: string;
  description: string | null;
  status: string;
  priority: number;
  due_date: string | null;
  metadata_json?: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
};

export type OpenLoopItem = {
  kind: "open_question" | "open_task" | "low_confidence_finding" | "unverified_claim";
  entity: "knowledge" | "task";
  id: UUID;
  title: string;
  reason: string;
};

export type ActivityEvent = {
  occurred_at: string;
  kind: "message" | "knowledge" | "artifact" | "task";
  entity_id: UUID;
  title: string;
  subtitle: string | null;
};

export type ProjectCommandCenter = {
  project_id: UUID;
  pinned_knowledge: KnowledgeItem[];
  key_findings: KnowledgeItem[];
  latest_conclusions: KnowledgeItem[];
  open_questions: KnowledgeItem[];
  next_tasks: TaskItem[];
  recent_artifacts: Artifact[];
  open_loops: OpenLoopItem[];
  timeline: ActivityEvent[];
};

export type DashboardSummary = {
  recent_projects: Project[];
  recent_knowledge: KnowledgeItem[];
  recent_artifacts: Artifact[];
  default_user_id: UUID;
};

export type SearchHit = {
  entity: "project" | "knowledge" | "artifact" | "message";
  id: UUID;
  project_id: UUID | null;
  title: string;
  snippet: string;
};
