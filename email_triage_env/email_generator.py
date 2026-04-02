"""Procedural email generator with ground-truth labels for deterministic grading."""

from __future__ import annotations

import random
from typing import List, Dict, Any

# ── Email Templates ────────────────────────────────────────────────────
# Each template: (sender, sender_title, subject, body, category, priority, department, keywords, attachments, fwd, cc, reply_depth)

TEMPLATES: List[Dict[str, Any]] = [
    # ── URGENT ─────────────────────────────────────────────────────────
    {
        "sender": "alerts@monitoring.internal",
        "sender_title": "System Alert",
        "subject": "CRITICAL: Production database CPU at 98%",
        "body": "Alert: prod-db-primary has sustained CPU utilization above 95% for 15 minutes. Queries are timing out. Immediate action required. Grafana dashboard: https://grafana.internal/d/db-health",
        "category": "urgent",
        "priority": 1,
        "department": "engineering",
        "keywords": ["production", "database", "cpu", "critical", "timeout"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "sarah.chen@company.com",
        "sender_title": "CEO",
        "subject": "RE: Board meeting prep - URGENT",
        "body": "Team, the board meeting has been moved to tomorrow 9 AM. I need the Q3 revenue deck updated with the latest numbers by tonight. This is top priority. Please confirm receipt.",
        "category": "urgent",
        "priority": 1,
        "department": "executive",
        "keywords": ["board", "meeting", "revenue", "deck", "tonight", "priority"],
        "attachments": False, "forwarded": False, "cc": ["cfo@company.com"], "reply_depth": 2,
    },
    {
        "sender": "security@company.com",
        "sender_title": "Security Operations",
        "subject": "SECURITY INCIDENT: Unauthorized access attempt detected",
        "body": "Our IDS flagged 47 failed login attempts from IP 203.0.113.42 targeting the admin panel in the last hour. The source IP has been geo-located to an unusual region. We've temporarily blocked the IP but need a full investigation. Please escalate immediately.",
        "category": "urgent",
        "priority": 1,
        "department": "engineering",
        "keywords": ["security", "unauthorized", "login", "incident", "blocked"],
        "attachments": True, "forwarded": False, "cc": ["ciso@company.com"], "reply_depth": 0,
    },
    {
        "sender": "ops-pager@company.com",
        "sender_title": "PagerDuty",
        "subject": "Payment processing service DOWN — customers impacted",
        "body": "Service payment-gateway is returning HTTP 503 since 14:32 UTC. Stripe webhook callbacks are failing. ~230 transactions are stuck. Revenue impact estimated at $45K/hour. On-call engineer has been paged.",
        "category": "urgent",
        "priority": 1,
        "department": "engineering",
        "keywords": ["payment", "down", "customers", "revenue", "503"],
        "attachments": False, "forwarded": False, "cc": ["vp-eng@company.com"], "reply_depth": 0,
    },
    {
        "sender": "legal-urgent@company.com",
        "sender_title": "General Counsel",
        "subject": "URGENT: Regulatory compliance deadline tomorrow",
        "body": "We have a mandatory filing with the SEC due by 5 PM ET tomorrow. The financial data section is incomplete. I need engineering to export the transaction logs for Q3. Failure to file on time results in significant penalties.",
        "category": "urgent",
        "priority": 1,
        "department": "legal",
        "keywords": ["regulatory", "compliance", "deadline", "SEC", "filing", "penalties"],
        "attachments": True, "forwarded": False, "cc": ["cfo@company.com"], "reply_depth": 1,
    },

    # ── ACTION REQUIRED ────────────────────────────────────────────────
    {
        "sender": "jira@company.atlassian.net",
        "sender_title": "Jira Notification",
        "subject": "[JIRA] PROJ-4521 assigned to you: Fix pagination bug in dashboard",
        "body": "You have been assigned PROJ-4521. Description: The analytics dashboard pagination breaks when filtering by date range > 90 days. Steps to reproduce attached. Priority: High. Sprint: Current.",
        "category": "action_required",
        "priority": 2,
        "department": "engineering",
        "keywords": ["jira", "assigned", "bug", "pagination", "dashboard", "fix"],
        "attachments": True, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "hr@company.com",
        "sender_title": "HR Department",
        "subject": "Action Required: Complete your annual benefits enrollment by Friday",
        "body": "Open enrollment for 2025 benefits closes this Friday at 11:59 PM. Please log into Workday to review and confirm your selections for health, dental, vision, and 401k. If no changes are made, your current elections will roll over. Contact hr-benefits@company.com with questions.",
        "category": "action_required",
        "priority": 3,
        "department": "hr",
        "keywords": ["benefits", "enrollment", "workday", "health", "deadline"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "mike.ross@company.com",
        "sender_title": "Engineering Manager",
        "subject": "Please review: Q3 performance self-assessment",
        "body": "Hi, performance review season is here. Please complete your self-assessment in Lattice by end of next week. Focus on your key accomplishments, areas for growth, and goals for Q4. Your manager review will follow.",
        "category": "action_required",
        "priority": 3,
        "department": "hr",
        "keywords": ["performance", "review", "self-assessment", "goals", "lattice"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "procurement@company.com",
        "sender_title": "Procurement",
        "subject": "Approval needed: Software license renewal — DataDog ($48K/yr)",
        "body": "The annual DataDog license renewal is due. Total cost: $48,000/year for 25 seats. This is a 12% increase from last year. Please approve or suggest alternatives by Wednesday. Budget code: ENG-TOOLS-2025.",
        "category": "action_required",
        "priority": 2,
        "department": "engineering",
        "keywords": ["approval", "license", "renewal", "datadog", "budget"],
        "attachments": True, "forwarded": False, "cc": ["finance@company.com"], "reply_depth": 0,
    },
    {
        "sender": "compliance@company.com",
        "sender_title": "Compliance Team",
        "subject": "Required: Complete annual security awareness training",
        "body": "As per company policy, all employees must complete the annual cybersecurity awareness training module. Please complete it through the LMS portal by the end of this month. Non-completion will be flagged to your manager.",
        "category": "action_required",
        "priority": 3,
        "department": "hr",
        "keywords": ["training", "security", "required", "compliance", "annual"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "pr-bot@github.com",
        "sender_title": "GitHub",
        "subject": "[PR #892] Review requested: Refactor authentication middleware",
        "body": "alice-dev requested your review on PR #892.\n\nChanges: Refactored auth middleware to support OAuth2 PKCE flow. 340 lines changed across 8 files. Tests passing. No breaking changes expected but auth is critical path.\n\nPlease review at your earliest convenience.",
        "category": "action_required",
        "priority": 2,
        "department": "engineering",
        "keywords": ["review", "pull request", "authentication", "refactor", "OAuth"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },

    # ── INFORMATIONAL ──────────────────────────────────────────────────
    {
        "sender": "newsletter@techcrunch.com",
        "sender_title": "TechCrunch",
        "subject": "This Week in AI: New breakthroughs in reasoning models",
        "body": "Top stories this week: 1) OpenAI releases GPT-5 Turbo with improved reasoning. 2) Google DeepMind achieves new SOTA on MATH benchmark. 3) EU passes comprehensive AI regulation framework. Read more at techcrunch.com/ai-weekly.",
        "category": "informational",
        "priority": 5,
        "department": "trash",
        "keywords": ["newsletter", "AI", "weekly", "news"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "all-hands@company.com",
        "sender_title": "Internal Comms",
        "subject": "All-Hands Recording: Q3 Results & Q4 Roadmap",
        "body": "Hi everyone, the recording of yesterday's all-hands meeting is now available on Confluence. Key highlights: Q3 revenue up 18% YoY, new enterprise plan launching in November, engineering headcount growing by 15 in Q4. Link: confluence.internal/all-hands-q3",
        "category": "informational",
        "priority": 4,
        "department": "executive",
        "keywords": ["all-hands", "recording", "results", "roadmap", "revenue"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "devops@company.com",
        "sender_title": "DevOps Team",
        "subject": "FYI: Scheduled maintenance window Saturday 2-4 AM UTC",
        "body": "Planned maintenance: We will be upgrading the Kubernetes cluster to v1.28 this Saturday between 2:00-4:00 AM UTC. Expected downtime: ~15 minutes for internal staging environments. Production will not be affected. No action required.",
        "category": "informational",
        "priority": 4,
        "department": "engineering",
        "keywords": ["maintenance", "scheduled", "kubernetes", "upgrade", "downtime"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "facilities@company.com",
        "sender_title": "Office Management",
        "subject": "Office kitchen renovation — temporary relocation of coffee machines",
        "body": "The 3rd floor kitchen will be under renovation from Oct 14-28. During this time, coffee machines and the microwave will be relocated to the 2nd floor break room. We apologize for the inconvenience.",
        "category": "informational",
        "priority": 5,
        "department": "hr",
        "keywords": ["kitchen", "renovation", "coffee", "temporary"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "release-notes@company.com",
        "sender_title": "Release Engineering",
        "subject": "Release v3.14.2 deployed to production",
        "body": "Version 3.14.2 has been successfully deployed. Changes: Fixed edge case in CSV export (#4401), improved API response caching (+30% faster), updated Node.js to 20 LTS. Rollback plan documented in the runbook. Monitoring dashboards show nominal metrics.",
        "category": "informational",
        "priority": 4,
        "department": "engineering",
        "keywords": ["release", "deployed", "production", "changelog", "monitoring"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "data-team@company.com",
        "sender_title": "Data Engineering",
        "subject": "Weekly data pipeline report — all green",
        "body": "All 47 scheduled ETL jobs completed successfully this week. Data freshness SLA met at 99.8%. One minor delay on the marketing attribution pipeline (resolved). Detailed report attached.",
        "category": "informational",
        "priority": 4,
        "department": "engineering",
        "keywords": ["data", "pipeline", "report", "ETL", "weekly"],
        "attachments": True, "forwarded": False, "cc": [], "reply_depth": 0,
    },

    # ── SPAM / PHISHING ────────────────────────────────────────────────
    {
        "sender": "prince.nigeria@royalmail.ng",
        "sender_title": None,
        "subject": "CONGRATULATIONS! You Have Won $5,000,000 USD",
        "body": "Dear Beloved, I am Prince Adebayo of the Royal Nigerian Heritage Fund. You have been selected to receive $5,000,000 USD. To claim your prize, please send your bank details and a processing fee of $500 to our secure portal.",
        "category": "spam",
        "priority": 5,
        "department": "trash",
        "keywords": ["congratulations", "won", "prince", "bank details", "fee"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "support@amaz0n-security.com",
        "sender_title": None,
        "subject": "Your Amazon account has been compromised — verify now",
        "body": "Dear Customer, We detected unauthorized activity on your Amazon account. Your account will be suspended within 24 hours unless you verify your identity. Click here to verify: http://amaz0n-security.phishing.site/verify. Amazon Security Team.",
        "category": "spam",
        "priority": 5,
        "department": "trash",
        "keywords": ["amazon", "compromised", "verify", "suspended", "phishing"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "deals@super-discount-pills.biz",
        "sender_title": None,
        "subject": "LIMITED TIME: 90% OFF Premium Supplements!!!",
        "body": "AMAZING DEAL! Get premium health supplements at 90% discount! Only today! Buy now at www.super-discount-pills.biz. Unsubscribe? Not possible! This is a one-time offer you CANNOT miss!!!",
        "category": "spam",
        "priority": 5,
        "department": "trash",
        "keywords": ["discount", "pills", "limited", "buy now", "supplements"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "admin@company-payroll.net",
        "sender_title": "IT Department",
        "subject": "Payroll system update — please re-enter your credentials",
        "body": "Dear Employee, We have upgraded our payroll system. For security purposes, please re-enter your login credentials and banking information at: http://company-payroll.net/update. This must be completed within 48 hours to avoid delays in your next paycheck. Thank you, IT Department.",
        "category": "spam",
        "priority": 5,
        "department": "trash",
        "keywords": ["payroll", "credentials", "banking", "re-enter", "phishing"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "marketing@random-saas-tool.io",
        "sender_title": None,
        "subject": "10x your productivity with AI-powered workflow automation",
        "body": "Hi there! I noticed your company could benefit from our AI-powered workflow automation platform. We've helped 500+ companies save 20 hours/week. Book a demo at calendly.com/random-saas/demo. P.S. We integrate with Slack, Jira, and everything else!",
        "category": "spam",
        "priority": 5,
        "department": "trash",
        "keywords": ["productivity", "AI-powered", "demo", "cold email", "unsolicited"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },

    # ── MEETING ────────────────────────────────────────────────────────
    {
        "sender": "calendar@google.com",
        "sender_title": "Google Calendar",
        "subject": "Invitation: Sprint Planning — Monday 10 AM",
        "body": "You've been invited to Sprint Planning.\nWhen: Monday, Oct 14, 2025 10:00 AM - 11:00 AM EST\nWhere: Zoom (link in calendar)\nOrganizer: mike.ross@company.com\nAgenda: Review backlog, assign stories for Sprint 47, discuss blockers.",
        "category": "meeting",
        "priority": 3,
        "department": "engineering",
        "keywords": ["sprint", "planning", "invitation", "zoom", "backlog"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "calendar@google.com",
        "sender_title": "Google Calendar",
        "subject": "Invitation: 1:1 with your manager — Wednesday 2 PM",
        "body": "You've been invited to a recurring 1:1.\nWhen: Wednesday, Oct 16, 2025 2:00 PM - 2:30 PM EST\nOrganizer: mike.ross@company.com\nNotes: Discuss project progress, career development, any blockers.",
        "category": "meeting",
        "priority": 3,
        "department": "engineering",
        "keywords": ["1:1", "manager", "recurring", "career", "progress"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "lisa.wong@company.com",
        "sender_title": "Product Manager",
        "subject": "Can we sync on the API redesign? Free Thursday afternoon?",
        "body": "Hey, I'd like to discuss the API v3 redesign proposal before the architecture review next week. Are you free Thursday afternoon? I'll send a calendar invite once confirmed. Main topics: breaking changes, migration timeline, client SDK updates.",
        "category": "meeting",
        "priority": 3,
        "department": "engineering",
        "keywords": ["sync", "API", "redesign", "meeting", "Thursday"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 1,
    },
    {
        "sender": "calendar@google.com",
        "sender_title": "Google Calendar",
        "subject": "Invitation: Customer onboarding call — Acme Corp",
        "body": "You've been invited to Customer Onboarding - Acme Corp.\nWhen: Friday, Oct 18, 2025 3:00 PM - 4:00 PM EST\nWhere: Google Meet\nOrganizer: sales-team@company.com\nNotes: Technical walkthrough of the integration for Acme's dev team. Prepare demo environment.",
        "category": "meeting",
        "priority": 2,
        "department": "sales",
        "keywords": ["customer", "onboarding", "Acme", "demo", "integration"],
        "attachments": False, "forwarded": False, "cc": ["acme-tech@acme.com"], "reply_depth": 0,
    },
    {
        "sender": "board-secretary@company.com",
        "sender_title": "Board Secretary",
        "subject": "Invitation: Emergency Board Call — Acquisition Discussion",
        "body": "An emergency board meeting has been scheduled.\nWhen: Today, 5:00 PM EST\nWhere: Secure Zoom (link sent separately)\nAgenda: Discussion of acquisition offer from MegaCorp. Attendance mandatory for all executives. Materials attached under NDA.",
        "category": "meeting",
        "priority": 1,
        "department": "executive",
        "keywords": ["board", "emergency", "acquisition", "mandatory", "NDA"],
        "attachments": True, "forwarded": False, "cc": [], "reply_depth": 0,
    },

    # ── AMBIGUOUS / HARD EMAILS ────────────────────────────────────────
    {
        "sender": "john.smith@partner-company.com",
        "sender_title": "Integration Partner",
        "subject": "RE: RE: RE: API rate limiting discussion",
        "body": "Following up on our thread from last week. Our team is still hitting 429 errors during peak hours. Can we get the rate limit increased from 100 to 500 req/min for our partner tier? We're losing about 15% of webhook deliveries. This is starting to affect our mutual customers.",
        "category": "action_required",
        "priority": 2,
        "department": "engineering",
        "keywords": ["API", "rate limit", "partner", "429", "webhook"],
        "attachments": False, "forwarded": False, "cc": ["partnerships@company.com"], "reply_depth": 4,
    },
    {
        "sender": "anonymous-tip@protonmail.com",
        "sender_title": None,
        "subject": "Potential compliance violation in sales team",
        "body": "I want to report that certain members of the sales team are offering unauthorized discounts exceeding the approved threshold to close Q3 deals. This may violate our revenue recognition policies. I prefer to remain anonymous but wanted to bring this to the right people.",
        "category": "urgent",
        "priority": 2,
        "department": "legal",
        "keywords": ["compliance", "violation", "sales", "unauthorized", "discounts", "anonymous"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "maria.garcia@company.com",
        "sender_title": "Senior Engineer",
        "subject": "Thoughts on migrating to microservices?",
        "body": "Hey team, I've been thinking about our monolith and whether we should start breaking it up. I put together a rough proposal doc. It's not urgent at all — just wanted to plant the seed for our next architecture discussion. Happy to chat whenever. Doc: confluence.internal/microservices-proposal",
        "category": "informational",
        "priority": 4,
        "department": "engineering",
        "keywords": ["microservices", "migration", "architecture", "proposal", "monolith"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "vendor-support@cloudprovider.com",
        "sender_title": "Cloud Provider Support",
        "subject": "FW: Your support ticket #78234 — resolution update",
        "body": "Hi, we've investigated the intermittent latency spikes you reported on your us-east-1 instances. Root cause: a noisy neighbor issue on the underlying hypervisor. We've live-migrated your VMs to dedicated hosts. Please monitor for 48 hours and confirm the issue is resolved. If the problem persists, we can schedule a call with our infrastructure team.",
        "category": "action_required",
        "priority": 3,
        "department": "engineering",
        "keywords": ["support", "ticket", "latency", "resolved", "monitor", "cloud"],
        "attachments": False, "forwarded": True, "cc": [], "reply_depth": 2,
    },
    {
        "sender": "recruiter@linkedin.com",
        "sender_title": "LinkedIn Recruiter",
        "subject": "Exciting opportunity at a Series B startup!",
        "body": "Hi! I came across your profile and was impressed by your experience. We're a fast-growing Series B startup revolutionizing the fintech space. We're looking for senior engineers who love solving hard problems. Interested in a confidential chat? Compensation: $250K-$350K + equity.",
        "category": "spam",
        "priority": 5,
        "department": "trash",
        "keywords": ["recruiter", "opportunity", "startup", "equity", "unsolicited"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "finance@company.com",
        "sender_title": "Finance Department",
        "subject": "Expense report Q3-4521 requires additional documentation",
        "body": "Your expense report Q3-4521 for $2,340 (conference travel) has been flagged for review. Please provide: 1) Itemized hotel receipt, 2) Conference registration confirmation, 3) Manager pre-approval form. Submit via Concur by Friday or the reimbursement will be delayed.",
        "category": "action_required",
        "priority": 3,
        "department": "hr",
        "keywords": ["expense", "report", "documentation", "receipts", "reimbursement"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "cto@company.com",
        "sender_title": "CTO",
        "subject": "FW: Competitor just launched a feature we've been planning",
        "body": "FYI — see the ProductHunt launch below. CompetitorX just shipped real-time collaboration, which is on our H1 2026 roadmap. Not panicking, but let's discuss in tomorrow's leadership sync whether we need to accelerate this. Would appreciate your technical feasibility assessment.",
        "category": "action_required",
        "priority": 2,
        "department": "engineering",
        "keywords": ["competitor", "feature", "roadmap", "accelerate", "feasibility"],
        "attachments": False, "forwarded": True, "cc": ["vp-product@company.com"], "reply_depth": 1,
    },
    {
        "sender": "noreply@company.com",
        "sender_title": "CI/CD Pipeline",
        "subject": "Build #12847 FAILED on main branch",
        "body": "Build #12847 triggered by commit abc1234 has failed.\n\nFailed step: integration-tests\nError: TimeoutError in test_payment_flow (exceeded 30s)\nCommit author: dev-bob@company.com\nBranch: main\n\nThis is a blocking failure — merges to main are paused until resolved.",
        "category": "action_required",
        "priority": 2,
        "department": "engineering",
        "keywords": ["build", "failed", "CI/CD", "integration", "blocking"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "customer-escalation@company.com",
        "sender_title": "Customer Success",
        "subject": "ESCALATION: Enterprise customer Acme threatening to churn",
        "body": "Acme Corp ($500K ARR) has raised a P1 escalation. Their API integration has been failing intermittently for 3 weeks. They've already contacted their account executive about not renewing. CEO of Acme wants a resolution plan by end of business today. This needs engineering + sales alignment ASAP.",
        "category": "urgent",
        "priority": 1,
        "department": "support",
        "keywords": ["escalation", "enterprise", "churn", "ARR", "failing", "resolution"],
        "attachments": False, "forwarded": False, "cc": ["sales-vp@company.com", "cto@company.com"], "reply_depth": 0,
    },
    {
        "sender": "design-team@company.com",
        "sender_title": "Design Lead",
        "subject": "New brand guidelines published — please review",
        "body": "Hi all, we've finalized the updated brand guidelines. Key changes: new color palette (moving from blue #2563EB to violet #7C3AED), updated logo usage rules, and new email signature templates. Please update your materials over the next two weeks. Full guide: figma.com/company-brand-2025.",
        "category": "informational",
        "priority": 4,
        "department": "hr",
        "keywords": ["brand", "guidelines", "color", "logo", "design"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "security@company-internal.xyz",
        "sender_title": "IT Security",
        "subject": "Important: Password reset required for all employees",
        "body": "Due to a recent security audit, all employees must reset their passwords immediately. Please click the link below to reset your corporate password: https://company-internal.xyz/reset-password. Note: Your account will be locked if not completed within 24 hours. — IT Security Team",
        "category": "spam",
        "priority": 5,
        "department": "trash",
        "keywords": ["password", "reset", "phishing", "suspicious domain", "locked"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "alex.kumar@company.com",
        "sender_title": "Tech Lead",
        "subject": "RFC: Implementing event-driven architecture for notifications",
        "body": "I've drafted an RFC for moving our notification system from polling to event-driven architecture using Kafka. This would reduce notification latency from ~30s to <1s and eliminate 40% of our unnecessary API calls. Draft is in the engineering wiki — would appreciate feedback before next Thursday's architecture review.",
        "category": "action_required",
        "priority": 3,
        "department": "engineering",
        "keywords": ["RFC", "event-driven", "Kafka", "architecture", "review", "feedback"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "charity@save-the-oceans.org",
        "sender_title": None,
        "subject": "Make a difference today — donate to ocean conservation",
        "body": "Dear Friend, our oceans are in crisis. Join 100,000+ supporters who have helped us remove 2 million pounds of plastic from the ocean. Your $25 donation can save 500 sea creatures. Donate now: save-the-oceans.org/donate. Together we can make a difference!",
        "category": "spam",
        "priority": 5,
        "department": "trash",
        "keywords": ["donate", "charity", "unsolicited", "ocean"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "intern-program@company.com",
        "sender_title": "Internship Coordinator",
        "subject": "Summer 2025 intern presentations — schedule attached",
        "body": "Hi team, our summer interns will be presenting their projects next Friday. Schedule attached. Each presentation is 15 minutes + 5 minutes Q&A. Your attendance would be greatly appreciated! Snacks will be provided. RSVP to this email by Wednesday.",
        "category": "informational",
        "priority": 4,
        "department": "hr",
        "keywords": ["intern", "presentations", "schedule", "summer"],
        "attachments": True, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "sales-ops@company.com",
        "sender_title": "Sales Operations",
        "subject": "Q3 pipeline review — your deals need updated close dates",
        "body": "Hi, as part of our quarterly pipeline hygiene, we've identified 7 deals in your pipeline with close dates in the past. Please update the expected close dates in Salesforce by end of Wednesday. Accurate forecasting depends on clean data. Reach out if any deal status has changed.",
        "category": "action_required",
        "priority": 3,
        "department": "sales",
        "keywords": ["pipeline", "deals", "salesforce", "close dates", "update"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "customer@enterprise-client.com",
        "sender_title": "Technical Lead, EnterpriseCo",
        "subject": "RE: RE: Data migration support request",
        "body": "Thanks for the migration script you sent. We ran it against our staging environment and it mostly works, but we're seeing data type mismatches in the 'metadata' column — our legacy system stores it as XML but the new schema expects JSON. Can your team provide a conversion utility? We'd like to go live next month.",
        "category": "action_required",
        "priority": 2,
        "department": "support",
        "keywords": ["migration", "data", "conversion", "XML", "JSON", "customer"],
        "attachments": False, "forwarded": False, "cc": ["support-eng@company.com"], "reply_depth": 3,
    },
    {
        "sender": "diversity@company.com",
        "sender_title": "D&I Committee",
        "subject": "Join us: Diwali celebration in the office — Oct 25th",
        "body": "You're invited to celebrate Diwali with your colleagues! Date: October 25th, 12-2 PM in the main cafeteria. Activities: Traditional lamp making, henna art, and an incredible lunch spread featuring authentic Indian cuisine. All are welcome! RSVP link included.",
        "category": "informational",
        "priority": 5,
        "department": "hr",
        "keywords": ["Diwali", "celebration", "office", "event", "cultural"],
        "attachments": False, "forwarded": False, "cc": [], "reply_depth": 0,
    },
    {
        "sender": "aws-notifications@amazon.com",
        "sender_title": "AWS",
        "subject": "AWS Cost Alert: Your estimated charges exceed $10,000",
        "body": "Your estimated AWS charges for the current billing period have exceeded $10,000, which is 150% of your budget threshold. Top cost drivers: EC2 instances ($6,200), RDS ($2,100), S3 ($1,700). Review your resources at console.aws.amazon.com/billing.",
        "category": "action_required",
        "priority": 2,
        "department": "engineering",
        "keywords": ["AWS", "cost", "alert", "billing", "budget", "exceeded"],
        "attachments": False, "forwarded": False, "cc": ["finance@company.com"], "reply_depth": 0,
    },
]


def generate_emails_for_task(task_id: str, seed: int = 42) -> List[Dict[str, Any]]:
    """Generate a deterministic email batch for a given task.

    Returns a list of email dicts each with ground_truth labels.
    """
    rng = random.Random(seed)

    if task_id == "easy_triage":
        # Pick 5 clear-cut emails — one from each category
        indices = _pick_clear_emails(rng, count=5)
    elif task_id == "medium_triage":
        # Pick 10 mixed emails — some ambiguous
        indices = _pick_mixed_emails(rng, count=10)
    elif task_id == "hard_triage":
        # Pick 15 emails — including the hardest ambiguous ones
        indices = _pick_hard_emails(rng, count=15)
    else:
        raise ValueError(f"Unknown task_id: {task_id}")

    emails = []
    for i, idx in enumerate(indices):
        t = TEMPLATES[idx]
        emails.append({
            "email_id": f"{task_id}_email_{i:03d}",
            "sender": t["sender"],
            "sender_title": t["sender_title"],
            "subject": t["subject"],
            "body": t["body"],
            "timestamp": f"2025-10-{14 + i % 7:02d}T{9 + i % 8:02d}:00:00Z",
            "has_attachments": t["attachments"],
            "reply_chain_length": t["reply_depth"],
            "cc_list": t.get("cc", []),
            "is_forwarded": t.get("forwarded", False),
            # Ground truth for grading
            "ground_truth": {
                "category": t["category"],
                "priority": t["priority"],
                "department": t["department"],
                "keywords": t["keywords"],
            },
        })

    return emails


def _pick_clear_emails(rng: random.Random, count: int) -> List[int]:
    """Pick clearly-categorized emails (one per category for easy task)."""
    # Group by category
    by_category = {}
    for i, t in enumerate(TEMPLATES):
        cat = t["category"]
        # Only pick the most obvious ones (no reply chains, clear signals)
        if t["reply_depth"] == 0 and not t.get("forwarded", False):
            by_category.setdefault(cat, []).append(i)

    picked = []
    categories = ["urgent", "action_required", "informational", "spam", "meeting"]
    for cat in categories:
        candidates = by_category.get(cat, [])
        if candidates:
            picked.append(rng.choice(candidates))

    # Fill remaining if needed
    while len(picked) < count:
        idx = rng.randint(0, len(TEMPLATES) - 1)
        if idx not in picked:
            picked.append(idx)

    return picked[:count]


def _pick_mixed_emails(rng: random.Random, count: int) -> List[int]:
    """Pick a mix of clear and ambiguous emails for medium task."""
    clear = _pick_clear_emails(rng, 5)
    remaining = [i for i in range(len(TEMPLATES)) if i not in clear]
    rng.shuffle(remaining)
    mixed = clear + remaining[:count - 5]
    rng.shuffle(mixed)
    return mixed[:count]


def _pick_hard_emails(rng: random.Random, count: int) -> List[int]:
    """Pick the hardest emails — reply chains, forwarded, ambiguous."""
    # Prioritize hard emails (reply chains, phishing, forwarded)
    hard_indices = []
    normal_indices = []
    for i, t in enumerate(TEMPLATES):
        if t["reply_depth"] >= 2 or t.get("forwarded", False) or t["category"] == "spam":
            hard_indices.append(i)
        else:
            normal_indices.append(i)

    rng.shuffle(hard_indices)
    rng.shuffle(normal_indices)

    picked = hard_indices[:min(len(hard_indices), count)]
    while len(picked) < count and normal_indices:
        picked.append(normal_indices.pop())

    rng.shuffle(picked)
    return picked[:count]
