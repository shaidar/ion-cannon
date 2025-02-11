# src/ion_cannon/config/settings.py
import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # Optional API keys that read from environment
    OPENAI_API_KEY: Optional[str] = Field(
        description="OpenAI API key for GPT models",
        default_factory=lambda: os.getenv("OPENAI_API_KEY")
    )

    # Default configurations
    LLM_PROVIDER: str = "ollama"
    LLM_MODEL: str = "mistral:instruct"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS_RESPONSE: int = 131072
    LLM_VALIDATOR_CONFIDENCE: float = 0.5  # Default confidence for fallbacks
    LLM_CONFIDENCE_THRESHOLD: float = 0.9  # Minimum confidence required to consider valid
    
    # Multi-LLM Configuration
    VALIDATOR1_PROVIDER: str = "ollama"
    VALIDATOR1_MODEL: str = "mistral:instruct"
    VALIDATOR2_PROVIDER: str = "ollama"
    VALIDATOR2_MODEL: str = "llama3.2:latest"
    SUMMARIZER_PROVIDER: str = "ollama"
    SUMMARIZER_MODEL: str = "mistral:instruct"

    # Directory Configuration
    BASE_DIR: Path = Path("./data")
    OUTPUT_DIR: Path = Path("./data/output")
    LOGS_DIR: Path = Path("./logs")
    
    # Reddit
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT: str = "ion_cannon"
    
    REDDIT_CHANNELS: List[str] = []
    REDDIT_POST_LIMIT: int = 30

    # Content Sources
    RSS_FEEDS: List[str] = [
        "http://export.arxiv.org/api/query?search_query=cs.AI&max_results=10",
        "http://export.arxiv.org/api/query?search_query=cs.CR&max_results=10",
        "http://export.arxiv.org/api/query?search_query=cs.SE&max_results=10",
        "http://feeds.feedburner.com/Talos",
        "https://adamlevin.com/feed/",
        "https://ai-techpark.com/category/cyber-security/feed",
        "https://apisecurity.io/feed/index.xml",
        "https://arstechnica.com/tag/security/feed/",
        "https://aws.amazon.com/blogs/machine-learning/feed",
        "https://aws.amazon.com/blogs/security/feed/",
        "https://aws.amazon.com/blogs/security/tag/artificial-intelligence/feed/",
        "https://be4sec.com/feed/",
        "https://www.blackfog.com/feed/",
        "https://blog.assetnote.io/feed.xml",
        "https://blog.huntr.com/rss.xml",
        "https://blog.isosceles.com/rss/",
        "https://blog.phylum.io/rss/",
        "https://blog.rapid7.com/rss/",
        "https://cacm-acm-org-preprod.go-vip.net/category/artificial-intelligence-machine-learning/feed",
        "https://cacm-acm-org-preprod.go-vip.net/category/security-and-privacy/feed",
        "https://cacm-acm-org-preprod.go-vip.net/section/news/feed",
        "https://daniel.haxx.se/blog/feed/",
        "https://embracethered.com/blog/index.xml",
        "https://feeds.feedburner.com/akamai/blog",
        "https://feeds.feedburner.com/govtech/blogs/lohrmann_on_infrastructure",
        "https://feeds.feedburner.com/nvidiablog",
        "https://feeds.feedburner.com/TheHackersNews",
        "https://gbhackers.com/feed/",
        "https://github.blog/tag/github-security-lab/feed/",
        "https://grahamcluley.com/feed/",
        "https://huggingface.co/blog/feed.xml",
        "https://isc.sans.edu/rssfeed_full.xml",
        "https://k12cybersecure.com/feed",
        "https://krebsonsecurity.com/feed/",
        "https://magazine.sebastianraschka.com/feed",
        "https://medium.com/feed/anton-on-security",
        "https://nao-sec.org/feed",
        "https://news.mit.edu/rss/school/mit-schwarzman-college-computing",
        "https://news.mit.edu/topic/mitcyber-security-rss.xml",
        "https://news.sophos.com/en-us/category/threat-research/feed/",
        "https://news4hackers.com/feed/",
        "https://portswigger.net/research/rss",
        "https://pulse.latio.tech/feed",
        "https://research.checkpoint.com/feed/",
        "https://rss.packetstormsecurity.com/",
        "https://samcurry.net/api/feed.rss",
        "https://scitechdaily.com/feed/",
        "https://securelist.com/feed/",
        "https://security.lauritz-holtmann.de/index.xml",
        "https://securityaffairs.co/wordpress/feed",
        "https://simonwillison.net/atom/everything/",
        "https://threatpost.com/feed/",
        "https://venturebeat.com/category/ai/feed/",
        "https://www.bellingcat.com/feed/",
        "https://www.bleepingcomputer.com/feed",
        "https://www.cio.com/category/security/index.rss",
        "https://www.cisa.gov/cybersecurity-advisories/all.xml",
        "https://www.cisecurity.org/feed/advisories",
        "https://www.cyberdefensemagazine.com/feed/",
        "https://www.darkreading.com/rss.xml",
        # Feed based on pre-configured Google Alert using same keywords
        "https://www.google.com/alerts/feeds/16646759326006124900/11716113568217286508",
        "https://www.google.com/alerts/feeds/16646759326006124900/8799745997790961988",
        ###########
        "https://www.hackerone.com/blog.rss",
        "https://www.hackread.com/feed/",
        "https://www.helpnetsecurity.com/feed/",
        "https://www.infosecurity-magazine.com/rss/news/",
        "https://www.kaspersky.com/blog/feed/",
        "https://www.knostic.ai/blog/rss.xml",
        "https://www.lastwatchdog.com/feed/",
        "https://www.legitsecurity.com/blog/rss.xml",
        "https://www.nist.gov/blogs/cybersecurity-insights/rss.xml",
        "https://www.schneier.com/blog/atom.xml",
        "https://www.securityweek.com/feed/",
        "https://www.theregister.com/security/cso/headlines.atom",
        "https://www.theregister.com/security/cyber_crime/headlines.atom",
        "https://www.theregister.com/security/patches/headlines.atom",
        "https://www.theregister.com/security/research/headlines.atom",
        "https://www.troyhunt.com/rss/",
        "https://www.welivesecurity.com/en/rss/feed/",
    ]
    
    # If list is modified, remember to modify Google Alert
    KEYWORDS: List[str] = [
        "ai security",
        "llm security",
        "machine learning security",
        "ai vulnerability",
        "llm vulnerability",
        "ai threat",
        "model security",
        "prompt injection",
        "adversarial ai",
        "ai attack",
        # Novel AI security threats
        "data poisoning",
        "backdoor attacks",
        "training pipeline tampering",
        "unintended data memorization",
        "adversarial dataset contamination",
        "model theft",
        "model inversion",
        "weight poisoning",
        "architecture leakage",
        "parameter-based attacks",
        "quantization vulnerabilities",
        "inference-time attacks",
        "output manipulation",
        "context window exploitation",
        "token-based attacks",
        "response format manipulation",
        "automation bias",
        "cascading failures",
        "emergent errors",
        "multi-agent system exploitation",
        "api chain manipulation",
        "decision boundary attacks",
        "goal misalignment amplification",
        "cross-model contamination",
        "capability transfer attacks",
        "fine-tuning vulnerabilities",
        "base model poisoning",
        "knowledge inheritance attacks",
    ]

# Global settings instance
settings = Settings()