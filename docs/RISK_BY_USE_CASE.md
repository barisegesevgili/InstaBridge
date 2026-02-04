# Risk by Use Case

**InstaBridge** uses two main components: **instagrapi** (Instagram API) and **Playwright** (WhatsApp Web). Risk depends heavily on *how* you use the tool. This document summarizes research on risk levels for the **intended use case**: downloading your own content (e.g. stories) at low frequency (e.g. once per day).

---

## Intended Use Case

- **What:** Download your own posts/stories and forward to WhatsApp.
- **Frequency:** Low (e.g. once per day).
- **No:** Likes, follows, DMs, scraping other users, or social-graph manipulation.

For this use case, the risk profile is **substantially lower** than for growth automation or spam-like behavior.

---

## instagrapi (Instagram API)

### Risk: **LOW → MEDIUM** for this use case

**Why the risk is lower here:**

| Factor | Effect |
|--------|--------|
| **Only your own content** | No access to other users' private data |
| **Very low frequency** (e.g. 1×/day) | Far below typical automation patterns |
| **No social manipulation** | No likes, follows, DMs |
| **No scraping of others** | No bulk fetching of third-party profiles |

Instagram’s enforcement focuses more on:

- Growth automation
- Spam-like interactions
- Abuse of social features

**You are doing none of that.**

**Remaining risks:**

- Private API usage still violates ToS
- Login via non-standard client can be flagged
- Future API/signature changes could increase detection

**Practical assessment:** For personal archival of your own stories at ~1×/day, instagrapi is commonly used and rarely punished at this cadence. Risk is **low to medium**, not zero.

---

## Playwright (WhatsApp Web)

### Risk: **VERY LOW** when used correctly

Playwright is the **safer** part of the stack for this use case.

**Why:**

- Behaves like a normal browser session
- You only access your own profile and content
- Flow is natural: view → download (human-like)
- Once per day is indistinguishable from manual use

**Conditions for “very low risk”:**

| Practice | Why it matters |
|----------|----------------|
| **Headed mode** (not headless) | Looks like a real browser |
| **Persistent browser profile** (cookies reused) | Same “device” over time |
| **No rapid clicking / looping** | Human-like pacing |
| **Run from your normal machine/IP** | Consistent, residential context |

If you follow these, the session is effectively indistinguishable from you manually downloading stories in a browser.

---

## Summary Table

| Component | General risk | For “own content, ~1×/day” | Notes |
|-----------|--------------|----------------------------|--------|
| **instagrapi** | Medium–High | **LOW → MEDIUM** | ToS violation; low frequency and no social abuse reduce risk. |
| **Playwright** | Low | **VERY LOW** | Headed, persistent profile, normal IP = like manual use. |

---

## Caveats

- **Not zero risk.** ToS is still violated; platforms can change detection at any time.
- **Use case matters.** High-frequency runs, other people’s content, or social actions increase risk.
- **Recommendation:** Prefer throwaway/test accounts for any automation; keep the option to use a primary account as an informed choice once you understand the above.

---

## Where to Read More

- [Safe Usage Guide](SAFE_USAGE_GUIDE.md) – Rate limiting, frequency, and safe patterns
- [Security Best Practices](SECURITY_BEST_PRACTICES.md) – Credentials and session safety
- [Legal Considerations](../LEGAL_CONSIDERATIONS.md) – ToS and legal context

*Last updated: 2026-02-04*
