# Safe Usage Guide - Minimizing Account Ban Risk

**InstaBridge** uses unofficial APIs that can trigger Instagram's bot detection. This guide helps you minimize the risk of account bans.

---

## 📋 **Risk by Use Case**

Risk depends strongly on *how* you use the tool:

| Use case | instagrapi risk | Playwright risk |
|----------|------------------|------------------|
| **Intended: own content, ~1×/day** | **LOW → MEDIUM** | **VERY LOW** (if headed, persistent profile, normal IP) |
| Growth automation, spam, scraping others | High | Higher |

For **personal archival** of your own stories at low frequency (e.g. once per day), with no likes/follows/DMs, risk is **substantially lower** than for automation that touches other users or runs often. See [Risk by use case](RISK_BY_USE_CASE.md) for the full research summary.

---

## ⚠️ **Critical: Understand the Risks**

### **What Can Happen:**
- 🚫 **Permanent account ban** - Most serious consequence (less likely at low frequency, own content only)
- ⏸️ **Temporary restrictions** - Rate limiting, feature blocks
- 🔒 **Account locks** - Verification challenges required
- ⚖️ **IP-level blocks** - Affects all accounts from your IP

### **Why This Happens:**
Instagram detects automation through:
- **Request patterns** - Too many requests too quickly
- **Behavioral patterns** - Inhuman timing and consistency
- **Session anomalies** - Suspicious login patterns
- **Volume spikes** - Sudden increases in activity

---

## 🛡️ **Built-in Rate Limiting (v1.0.1+)**

### **Automatic Protections:**

InstaBridge now includes **automatic rate limiting** on all Instagram API calls:

```python
# Pre-configured rate limiters:
CONSERVATIVE  # 3-7s delays, 40 req/hour (safest)
MODERATE      # 2-5s delays, 60 req/hour (default, balanced)
AGGRESSIVE    # 1-3s delays, 80 req/hour (higher risk)
```

**Default:** MODERATE rate limiter is active on all operations.

### **What's Protected:**
✅ Fetching posts (`get_latest_post_items`)
✅ Fetching stories (`get_active_story_items`)
✅ Downloading media (`download`)
✅ User stats fetching (analytics)
✅ Random jitter added to appear human-like

### **How It Works:**
```
Request 1 → [Wait 2-5s + random jitter] → Request 2 → [Wait...] → Request 3
           Also enforces max 60 requests per hour
```

---

## 📊 **Safe Usage Patterns**

### **1. Frequency Recommendations**

| Use Case | Safe Frequency | Max Daily Runs |
|----------|---------------|----------------|
| **New throwaway account** | Every 4-6 hours | 4 runs/day |
| **Established throwaway** | Every 2-4 hours | 6 runs/day |
| **Testing/Development** | Use `--dry-run` | Unlimited |
| **Analytics only** | Every 1-2 hours | 12 runs/day |

### **2. Schedule Patterns**

**❌ BAD (Suspicious):**
```bash
# Exactly every hour, on the hour (too regular)
0 * * * * python -m src.main

# Multiple runs in quick succession
python -m src.main && python -m src.main && python -m src.main
```

**✅ GOOD (Appears Human):**
```bash
# Random times with variation
python -m src.scheduler  # Uses configured time with natural delays

# Single runs, spaced out
# Run at: 09:15, 13:47, 18:22, 22:09 (irregular intervals)
```

### **3. Volume Guidelines**

**Per Run:**
- Max 5-10 new posts
- Max 15-20 stories
- Total < 25 items per run

**Per Day:**
- Max 50 posts checked
- Max 100 stories checked
- Max 200 total API requests

**If you exceed these:** Instagram may trigger rate limiting or suspicious activity flags.

---

## 🎯 **Recommended Configurations**

### **Configuration 1: Ultra-Safe (New Account)**

```bash
# .env
# Run once per day at random time
python -m src.run_at --time 14:30 --tz Europe/Berlin

# Wait 24 hours before next run
```

**Rate Limit:** CONSERVATIVE (3-7s delays)

```python
# In ig.py initialization:
from src.rate_limiter import RateLimits
ig._rate_limiter = RateLimits.CONSERVATIVE
```

### **Configuration 2: Balanced (Default)**

```bash
# Daily at consistent time but with built-in delays
python -m src.scheduler  # Runs at configured time (e.g., 19:00)
```

**Rate Limit:** MODERATE (2-5s delays) - **Active by default**

### **Configuration 3: Development/Testing**

```bash
# Use dry-run mode - no actual Instagram requests!
python -m src.main --dry-run

# Test frequently without risk
```

**Rate Limit:** Not needed (no real requests)

---

## 🚨 **Warning Signs & What To Do**

### **Warning Signs You're Being Detected:**

| Sign | Risk Level | Action |
|------|-----------|---------|
| Login challenges/captchas | 🟡 Medium | Stop for 24-48 hours |
| "Try again later" errors | 🟡 Medium | Stop for 12-24 hours |
| Explicit rate limit errors | 🟠 High | Stop for 48-72 hours |
| Account temporarily locked | 🔴 Critical | Stop for 1 week |
| Required phone verification | 🔴 Critical | Stop permanently |

### **Immediate Actions:**

1. **STOP all automation immediately**
2. **Don't try to circumvent** (makes it worse)
3. **Wait the recommended time**
4. **Switch to more conservative settings**
5. **Consider using a different throwaway account**

### **Recovery Protocol:**

```bash
# 1. Stop automation
# Kill all running instances

# 2. Wait period (48-72 hours minimum)

# 3. Manual Instagram app activity
# - Login via mobile app
# - View a few stories (manually)
# - Like a few posts (manually)
# - Wait another 24 hours

# 4. Resume with CONSERVATIVE settings
from src.rate_limiter import RateLimits
ig._rate_limiter = RateLimits.CONSERVATIVE
```

---

## 📱 **IP & Device Fingerprinting**

### **Best Practices:**

1. **Use residential IP** (not VPN/datacenter)
   ```bash
   # Instagram detects datacenter IPs
   # Use your home internet connection
   ```

2. **Consistent device** (don't switch constantly)
   ```bash
   # Stick to one computer/location
   # Frequent IP changes = suspicious
   ```

3. **Session persistence** (already implemented)
   ```bash
   # ig_session.json maintains session
   # Reduces suspicious re-authentications
   ```

---

## 🎲 **Randomization Strategies**

InstaBridge includes these randomization features:

### **1. Request Timing**
```python
# Random jitter between min and max delays
delay = random.uniform(min_delay, max_delay)
# Example: 2.7s, 3.4s, 4.1s (not exactly 3.0s every time)
```

### **2. Human-like Delays**
```python
# Small variations in download timing
human_like_delay(0.5, 1.5)
# Appears like a human clicking/waiting
```

### **3. Hourly Request Limits**
```python
# Enforces maximum requests per hour
# Prevents sudden spikes that trigger detection
```

---

## 📈 **Monitoring Your Usage**

### **Check Request Count:**

```bash
# View rate limiter status (in logs)
[rate_limiter] Hourly limit reached (60 req/hour). Waiting 1234.5s
```

### **Recommended Monitoring:**

```python
# Add to your monitoring:
- Total requests per hour
- Average delay between requests
- Login challenges encountered
- Rate limit errors received
```

---

## 🔧 **Advanced: Custom Rate Limiting**

### **Override Default Settings:**

```python
# In your main.py or custom script:
from src.rate_limiter import RateLimiter, set_global_rate_limit

# Create custom limiter (even more conservative)
custom_limiter = RateLimiter(
    min_delay=5.0,      # 5 second minimum
    max_delay=10.0,     # 10 second maximum
    requests_per_hour=30  # Only 30 requests per hour
)

# Apply globally
set_global_rate_limit(custom_limiter)
```

### **Per-Operation Control:**

```python
# Apply different limits to different operations
from src.rate_limiter import rate_limit

@rate_limit(min_delay=3.0, max_delay=8.0, requests_per_hour=40)
def my_sensitive_operation():
    # This function will be strictly rate-limited
    pass
```

---

## ✅ **Safe Usage Checklist**

Before each run:
- [ ] Using throwaway account (not primary)
- [ ] More than 2 hours since last run
- [ ] No recent Instagram errors or challenges
- [ ] Rate limiting is enabled (default in v1.0.1+)
- [ ] Reasonable volume expected (< 25 items)
- [ ] Consistent IP address (not switching)
- [ ] Session file exists (no re-authentication needed)

Daily:
- [ ] Total runs < 6 per day
- [ ] No rate limit errors encountered
- [ ] Account still accessible via mobile app
- [ ] No verification challenges

Weekly:
- [ ] Review rate limiter logs
- [ ] Check account health in Instagram app
- [ ] Adjust rate limits if needed
- [ ] Consider account rotation if issues arise

---

## 🎓 **Key Principles**

1. **Slower is Safer** - More delays = less detection risk
2. **Irregular is Better** - Random timing appears human
3. **Volume Matters** - Fewer requests = lower risk
4. **Patience Pays** - Wait out rate limits, don't fight them
5. **Throwaway Accounts** - Never risk your primary account
6. **Monitor Actively** - Watch for warning signs

---

## 📚 **Additional Resources**

- [Security Best Practices](SECURITY_BEST_PRACTICES.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [Architecture Documentation](ARCHITECTURE.md)

---

## ⚖️ **Legal Disclaimer**

This tool violates Instagram Terms of Service. You use it at your own risk. The developers are not responsible for:
- Account bans or restrictions
- Data loss
- Legal consequences
- Any other issues arising from use

**Use only for educational purposes with throwaway accounts.**

---

*Last Updated: 2026-02-04*  
*Version: 1.0.1+rate-limiting*
