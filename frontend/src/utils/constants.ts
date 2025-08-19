export const CHAT_MODES = {
  ASK: 'ask',
  RAG: 'rag',
  AGENT: 'agent',
} as const;

export const CHAT_MODE_LABELS = {
  [CHAT_MODES.ASK]: 'Ask',
  [CHAT_MODES.RAG]: 'RAG',
  [CHAT_MODES.AGENT]: 'Agent',
} as const;

export const CHAT_MODE_DESCRIPTIONS = {
  [CHAT_MODES.ASK]: 'General medical knowledge chat with AI',
  [CHAT_MODES.RAG]: 'Query against medicine database with sources',
  [CHAT_MODES.AGENT]: 'AI agent with tool access for research',
} as const;

export const PROVIDERS = {
  OPENAI: 'openai',
  AZURE: 'azure',
} as const;

export const PROVIDER_LABELS = {
  [PROVIDERS.OPENAI]: 'OpenAI',
  [PROVIDERS.AZURE]: 'Azure OpenAI',
} as const;

export const DEFAULT_MODELS = {
  [PROVIDERS.OPENAI]: 'gpt-4',
  [PROVIDERS.AZURE]: 'gpt-4',
} as const;

export const MEDICAL_DISCLAIMER = "This is not medical advice. Always consult with qualified healthcare professionals for medical decisions.";

export const SAMPLE_QUERIES = {
  [CHAT_MODES.ASK]: [
    "What is hypertension?",
    "Explain the difference between Type 1 and Type 2 diabetes",
    "What are the symptoms of pneumonia?",
    "How does the immune system work?",
  ],
  [CHAT_MODES.RAG]: [
    "What are the side effects of Augmentin 625?",
    "What is Azithral 500 tablet used for?",
    "What are substitutes for Allegra 120mg?",
    "Is Atarax 25mg habit forming?",
    "What class of drug is Ascoril LS syrup?",
    "Side effects of Azee 500 tablet",
  ],
  [CHAT_MODES.AGENT]: [
    "Search PubMed for recent studies on diabetes treatment",
    "Find the latest research on COVID-19 vaccines",
    "What are the current clinical trials for Alzheimer's disease?",
    "Search for drug interactions with Warfarin",
  ],
} as const;

export const MCP_SERVER_TYPES = [
  { value: 'web-browse', label: 'Web Browser', description: 'Search and browse web content' },
  { value: 'filesystem', label: 'File System', description: 'Read and write files' },
  { value: 'code-execution', label: 'Code Execution', description: 'Execute code in sandbox' },
  { value: 'calendar', label: 'Calendar', description: 'Calendar management' },
  { value: 'pubmed', label: 'PubMed', description: 'Medical literature search' },
  { value: 'neo4j', label: 'Neo4j', description: 'Graph database queries' },
  { value: 'marklogic', label: 'MarkLogic', description: 'Document database queries' },
] as const;
