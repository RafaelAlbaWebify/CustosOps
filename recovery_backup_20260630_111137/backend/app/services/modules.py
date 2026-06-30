from app.schemas.module import ModuleInfo


def get_modules() -> list[ModuleInfo]:
    return [
        ModuleInfo(
            id="dashboard",
            name="Dashboard",
            group="Core",
            status="foundation",
            description="CustosOps overview and posture summary.",
        ),
        ModuleInfo(
            id="endpoint-security",
            name="Endpoint Security Evidence",
            group="Endpoint",
            status="planned",
            description="Read-only Windows endpoint security posture evidence.",
        ),
        ModuleInfo(
            id="dns-hygiene",
            name="DNS and Infrastructure Hygiene",
            group="Infrastructure",
            status="foundation",`r`n            description="Read-only DNS and infrastructure hygiene evidence.",
        ),
        ModuleInfo(
            id="identity-m365",
            name="Identity and M365 Security Posture",
            group="Identity",
            status="planned",
            description="Microsoft 365 and Entra security posture evidence.",
        ),
        ModuleInfo(
            id="risk-prioritization",
            name="Risk and Vulnerability Prioritization",
            group="Risk",
            status="planned",
            description="Prioritized remediation guidance based on evidence.",
        ),
        ModuleInfo(
            id="reports",
            name="Reports and Runbooks",
            group="Evidence",
            status="planned",
            description="HTML, JSON, CSV, and Markdown report generation.",
        ),
    ]