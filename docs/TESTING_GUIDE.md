# 🧪 Testing Guide: Internet Search Integration

## 📋 Overview

This guide helps you test the newly implemented Internet Search functionality for the Formula Recognition Bot.

## 🚀 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

New dependencies added:
- `duckduckgo-search==6.3.5`
- `langchain-community==0.3.7`

### 2. Configure Environment

Update your `.env` file with search settings:

```env
# Search Configuration
ENABLE_SEARCH=true
SEARCH_MAX_RESULTS=5
SEARCH_CACHE_TTL=86400
```

### 3. Start the Bot

```bash
python -m src.main
```

Or with Docker:

```bash
docker-compose up --build
```

## 🧪 Test Cases

### Test Case 1: Common Formula (E=mc²)

**Steps:**
1. Send `/formula` command to bot
2. Upload image of Einstein's formula: E = mc²
3. Wait for response (~25-35 seconds)

**Expected Result:**
- Formula extracted correctly
- Internet search finds relevant information
- Response includes:
  - Formula explanation
  - Source citations (🌐 DuckDuckGo + 🤖 GigaChat)
  - Structured information

**Success Criteria:**
- ✅ Formula recognized
- ✅ Search results included
- ✅ Response time < 40 seconds

---

### Test Case 2: Physics Formula (F=ma)

**Steps:**
1. Send `/formula` command
2. Upload image of Newton's Second Law: F = ma
3. Wait for response

**Expected Result:**
- Formula: F = ma
- Search finds Newton's Second Law information
- Explanation includes force, mass, acceleration

**Success Criteria:**
- ✅ Correct formula extraction
- ✅ Relevant search results
- ✅ Complete explanation

---

### Test Case 3: Math Formula (Pythagorean Theorem)

**Steps:**
1. Send `/formula` command
2. Upload image: a² + b² = c²
3. Wait for response

**Expected Result:**
- Formula: a² + b² = c²
- Search finds Pythagorean theorem info
- Explanation includes triangle geometry

**Success Criteria:**
- ✅ Formula recognized
- ✅ Search context added
- ✅ Mathematical explanation provided

---

### Test Case 4: Cache Testing

**Steps:**
1. Send same formula twice (e.g., E=mc²)
2. Compare response times

**Expected Result:**
- First request: ~25-35 seconds (with search)
- Second request: ~20-25 seconds (cached search)

**Success Criteria:**
- ✅ Second request faster
- ✅ Same quality response
- ✅ Cache hit logged

---

### Test Case 5: Search Disabled

**Steps:**
1. Set `ENABLE_SEARCH=false` in `.env`
2. Restart bot
3. Send formula

**Expected Result:**
- Formula still recognized
- No search performed
- Only GigaChat explanation
- Source: 🤖 GigaChat AI only

**Success Criteria:**
- ✅ Bot works without search
- ✅ Faster response (~20-25s)
- ✅ No search errors

---

## 🔍 Verification Checklist

### Database Verification

Check that search cache table was created:

```bash
sqlite3 users.db
```

```sql
.tables
-- Should show: users, search_cache

.schema search_cache
-- Should show table structure

SELECT COUNT(*) FROM search_cache;
-- Should show cached entries after tests
```

### Log Verification

Check logs for proper chain execution:

```
Chain 1: Extracting formula from image
Chain 2: Searching internet for formula context
Chain 3: Generating comprehensive explanation
```

### Response Format Verification

Response should include:

```
✅ **Результат распознавания:**

📐 **[Formula Name]**
[Formula]

**Область применения:** [Field]

**Описание:**
[Description]

**Переменные:**
• [Variable explanations]

**Практическое применение:**
- [Applications]

**Пример:**
[Example]

---

**Источники информации:**
- 🌐 Интернет-поиск (DuckDuckGo)
- 🤖 GigaChat AI
```

## 🐛 Troubleshooting

### Issue: Search Not Working

**Symptoms:**
- No search results in response
- Only GigaChat source listed

**Solutions:**
1. Check `ENABLE_SEARCH=true` in `.env`
2. Verify internet connection
3. Check DuckDuckGo is accessible
4. Review logs for search errors

### Issue: Slow Response

**Symptoms:**
- Response takes > 40 seconds

**Solutions:**
1. Check internet speed
2. Verify GigaChat API status
3. Test with cached formula (should be faster)
4. Reduce `SEARCH_MAX_RESULTS` in config

### Issue: Cache Not Working

**Symptoms:**
- Same formula always takes same time
- No cache hits in logs

**Solutions:**
1. Check database file exists
2. Verify `search_cache` table created
3. Check `SEARCH_CACHE_TTL` setting
4. Review cache repository logs

### Issue: Import Errors

**Symptoms:**
```
ModuleNotFoundError: No module named 'duckduckgo_search'
```

**Solutions:**
```bash
pip install --upgrade -r requirements.txt
```

## 📊 Performance Metrics

Expected performance:

| Metric | Target | Acceptable |
|--------|--------|------------|
| First request (with search) | 25-35s | < 40s |
| Cached request | 20-25s | < 30s |
| Search disabled | 20-25s | < 30s |
| Cache hit rate | > 40% | > 20% |

## ✅ Test Completion Checklist

- [ ] All 5 test cases passed
- [ ] Database tables created correctly
- [ ] Cache working properly
- [ ] Search results appearing in responses
- [ ] Response format correct
- [ ] Performance within targets
- [ ] No errors in logs
- [ ] Bot works with search disabled

## 📝 Test Report Template

```markdown
# Test Report: Internet Search Integration

**Date:** [Date]
**Tester:** [Name]
**Environment:** [Local/Docker]

## Test Results

### Test Case 1: E=mc²
- Status: ✅ Pass / ❌ Fail
- Response Time: [X]s
- Notes: [Any observations]

### Test Case 2: F=ma
- Status: ✅ Pass / ❌ Fail
- Response Time: [X]s
- Notes: [Any observations]

### Test Case 3: a²+b²=c²
- Status: ✅ Pass / ❌ Fail
- Response Time: [X]s
- Notes: [Any observations]

### Test Case 4: Cache
- Status: ✅ Pass / ❌ Fail
- First: [X]s, Second: [Y]s
- Notes: [Any observations]

### Test Case 5: Search Disabled
- Status: ✅ Pass / ❌ Fail
- Response Time: [X]s
- Notes: [Any observations]

## Issues Found

[List any issues discovered]

## Recommendations

[Any suggestions for improvement]
```

---

**Ready to test! 🚀**