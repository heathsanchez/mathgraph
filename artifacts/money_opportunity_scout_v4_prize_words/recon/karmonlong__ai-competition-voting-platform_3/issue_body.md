# Create database schema and models with Supabase

## Objective
Design and implement a comprehensive database schema for the AI Competition Voting Platform using Supabase, including tables for users, competitions, submissions, votes, and related entities with proper relationships, constraints, and Supabase-specific features like Row Level Security (RLS) and real-time subscriptions.

## Technical Details

### Database Technology
- **Supabase (PostgreSQL)** as managed database service
- **Prisma ORM** with Supabase driver adapter
- **Supabase CLI** for migrations and type generation
- **Row Level Security (RLS)** for data protection
- **Real-time subscriptions** for live updates
- **Connection pooling** with Supabase Pooler

### Core Entities

#### Users (extends auth schema)
```sql
-- Extended from authentication system
ALTER TABLE users ADD COLUMN role VARCHAR(20) DEFAULT 'participant';
ALTER TABLE users ADD COLUMN bio TEXT;
ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);
ALTER TABLE users ADD COLUMN github_url VARCHAR(500);
ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
```

#### Competitions
```sql
CREATE TABLE competitions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    rules TEXT NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    submission_deadline TIMESTAMP NOT NULL,
    voting_start_date TIMESTAMP NOT NULL,
    voting_end_date TIMESTAMP NOT NULL,
    max_participants INTEGER,
    status VARCHAR(20) DEFAULT 'draft',
    prize_description TEXT,
    evaluation_criteria JSONB,
    organizer_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Submissions
```sql
CREATE TABLE submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competition_id UUID REFERENCES competitions(id) ON DELETE CASCADE,
    participant_id UUID REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    code_repository_url VARCHAR(500),
    demo_url VARCHAR(500),
    documentation_url VARCHAR(500),
    submission_data JSONB,
    status VARCHAR(20) DEFAULT 'submitted',
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(competition_id, participant_id)
);
```

#### Votes
```sql
CREATE TABLE votes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID REFERENCES submissions(id) ON DELETE CASCADE,
    voter_id UUID REFERENCES users(id) ON DELETE CASCADE,
    score INTEGER CHECK (score >= 1 AND score <= 10),
    criteria_scores JSONB,
    feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(submission_id, voter_id)
);
```

#### Competition Participants
```sql
CREATE TABLE competition_participants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    competition_id UUID REFERENCES competitions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'registered',
    UNIQUE(competition_id, user_id)
);
```

### Indexes and Performance
```sql
-- Performance indexes
CREATE INDEX idx_competitions_status ON competitions(status);
CREATE INDEX idx_competitions_dates ON competitions(start_date, end_date);
CREATE INDEX idx_submissions_competition ON submissions(competition_id);
CREATE INDEX idx_submissions_participant ON submissions(participant_id);
CREATE INDEX idx_votes_submission ON votes(submission_id);
CREATE INDEX idx_votes_voter ON votes(voter_id);
CREATE INDEX idx_competition_participants_competition ON competition_participants(competition_id);
CREATE INDEX idx_competition_participants_user ON competition_participants(user_id);
```

### Constraints and Triggers
- Check constraints for date validation (start < end)
- Prevent voting outside voting periods
- Ensure unique participant per competition
- Prevent self-voting
- Automatic timestamp updates
- Cascade deletes for related data

## Acceptance Criteria
- [ ] All tables created with proper relationships
- [ ] Foreign key constraints implemented
- [ ] Unique constraints for business rules
- [ ] Check constraints for data validation
- [ ] Indexes for query performance
- [ ] Database migrations created and tested
- [ ] Prisma schema definitions complete
- [ ] Seed data for development/testing
- [ ] Database connection pooling configured
- [ ] Backup and recovery procedures documented
- [ ] Query performance benchmarks
- [ ] Schema documentation generated

## Implementation Notes
- Use Supabase migrations for schema changes
- Implement Row Level Security (RLS) policies
- Add created_at/updated_at timestamps to all tables
- Use UUIDs for primary keys (security and scalability)
- Implement proper indexing strategy
- Consider partitioning for large tables (votes)
- Enable real-time subscriptions for votes and competitions
- Use Supabase Auth for user management integration
- Configure connection pooling with Supabase Pooler
- Set up database backups and Point-in-Time Recovery (PITR)

## Dependencies
- @supabase/supabase-js
- @prisma/client
- prisma
- supabase
- @supabase/auth-helpers-nextjs
- prisma-dbml-generator (for documentation)

## Prisma Models
```prisma
model User {
  id                String    @id @default(uuid())
  email             String    @unique
  passwordHash      String
  firstName         String?
  lastName          String?
  role              Role      @default(PARTICIPANT)
  bio               String?
  avatarUrl         String?
  githubUrl         String?
  emailVerified     Boolean   @default(false)
  isActive          Boolean   @default(true)
  createdAt         DateTime  @default(now())
  updatedAt         DateTime  @updatedAt
  
  organizedCompetitions Competition[] @relation("CompetitionOrganizer")
  submissions       Submission[]
  votes             Vote[]
  participants      CompetitionParticipant[]
  refreshTokens     RefreshToken[]
}
```

## Testing Requirements
- Unit tests for all model relationships
- Integration tests for CRUD operations
- Performance tests for large datasets
- Constraint validation tests
- Migration rollback tests
- Connection pool tests
- Query optimization tests
- Data integrity tests

## Supabase-Specific Features

### Row Level Security (RLS) Policies
```sql
-- Users can only see their own data
CREATE POLICY "Users can view own profile" ON users FOR SELECT USING (auth.uid() = id);

-- Competition organizers can manage their competitions
CREATE POLICY "Organizers can manage own competitions" ON competitions FOR ALL USING (auth.uid() = organizer_id);

-- Participants can only vote once per submission
CREATE POLICY "One vote per user per submission" ON votes FOR INSERT WITH CHECK (
  NOT EXISTS (SELECT 1 FROM votes WHERE submission_id = NEW.submission_id AND voter_id = auth.uid())
);
```

### Real-time Subscriptions
```typescript
// Subscribe to vote changes for real-time updates
const votesSubscription = supabase
  .from('votes')
  .on('INSERT', payload => {
    console.log('New vote received:', payload)
    // Update UI with new vote count
  })
  .subscribe()
```

### Database Configuration
```sql
-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";
CREATE EXTENSION IF NOT EXISTS "btree_gist";

-- Configure connection pooling
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
```

## Performance Considerations
- Index strategy for common queries
- Query optimization for leaderboards
- Pagination for large result sets
- Supabase connection pooling configuration
- Automatic caching with Supabase
- Partitioning strategy for votes table (by competition_id)
- Database maintenance procedures (auto-vacuum)
- Read replicas for analytics (Supabase project addon)

## Security Considerations
- Row-level security for user data
- Encryption for sensitive data
- Audit logging for data changes
- Backup encryption
- Access control for database connections
- SQL injection prevention through ORM
- Data masking for development environments
- GDPR compliance features (data deletion)