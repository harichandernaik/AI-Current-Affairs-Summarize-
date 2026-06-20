# UPSCBrief Database Schema

The app runs with MongoDB in production and a JSON fallback for local development.

## Collections

### users
- `_id`
- `email` unique
- `passwordHash`
- `createdAt`
- `lastLoginAt`

### profiles
- `_id`
- `userId` unique
- `fullName`
- `email`
- `targetYear`
- `optionalSubject`
- `state`
- `examType`

### news_articles
- `_id`
- `title`
- `source`
- `date`
- `content`
- `sourceType`
- `originalUrl`
- `category`
- `shortSummary`
- `detailedSummary`
- `keyFacts`
- `keywords`
- `importantTerms`
- `governmentSchemes`
- `constitutionalArticles`
- `committees`
- `reports`
- `internationalOrganizations`
- `mcqs`
- `mainsQuestions`
- `pyqs`

### question_bank
- `_id`
- `articleId`
- `kind`
- `question`
- `options`
- `answer`
- `explanation`
- `paper`
- `directive`
- `wordLimit`
- `modelAnswerPoints`

### pdf_uploads
- `_id`
- `filename`
- `source`
- `date`
- `pages`
- `engine`
- `createdCount`
- `ignoredCount`
- `batch`
- `uploadedAt`

### analytics
- `_id`
- `event`
- `userId`
- `metadata`
- `createdAt`

## Recommended Indexes

```javascript
db.users.createIndex({ email: 1 }, { unique: true });
db.profiles.createIndex({ userId: 1 }, { unique: true });
db.news_articles.createIndex({ date: -1, category: 1 });
db.news_articles.createIndex({ title: 1, date: 1 });
db.news_articles.createIndex({ originalUrl: 1 }, { sparse: true });
db.question_bank.createIndex({ articleId: 1, kind: 1 });
db.pdf_uploads.createIndex({ uploadedAt: -1 });
db.analytics.createIndex({ createdAt: -1, event: 1 });
```
