# SOL-LONG-MACH / 09_SYSTEMS / 01_DMARC

SOURCE: user-supplied Google Workspace procedure, SOL.txt, Hostinger DNS API reference.
CURRENT STATE: prepared; not published to DNS.

## Three stages
1. Provision and confirm a dedicated DMARC mailbox or group within the target domain.
2. Verify sender SPF/DKIM and third-party mail alignment. Google recommends 48h after enabling SPF/DKIM before DMARC.
3. Start with TXT name _dmarc and value v=DMARC1; p=none; rua=mailto:<confirmed-mailbox>; pct=100.

## @.env / .VSOL.ENV
Bind the live Hostinger credential in a private local secret store as HOSTINGER_API_TOKEN.
The example contains only reference names. Do not paste keys into GitHub, chat, logs or plugin packages.
Actual .VSOL.ENV must remain untracked.

Read-only inspection:
python 09_SYSTEMS/01_DMARC/hostinger_dmarc.py --domain <verified-domain> --report-mail <confirmed-mailbox>

After mailbox and SPF/DKIM have been checked:
python 09_SYSTEMS/01_DMARC/hostinger_dmarc.py --domain <verified-domain> --report-mail <confirmed-mailbox> --apply --mailbox-confirmed --auth-confirmed

Runner checks existing TXT records first, never replaces an existing DMARC,
uses overwrite=false, validates before update and performs provider readback.
Do not use DNS zone reset. Hostinger zone readback alone does not establish that
the domain uses Hostinger nameservers; independently check authoritative DNS.

UNRESOLVED: correct domain, confirmed mailbox, actual Hostinger API connectivity,
SPF/DKIM readiness, authoritative DNS publication.
No tmt/temp writes; no secret bytes in this repository.
