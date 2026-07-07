# Prize Recon Report

## Verdict

`PARK_RISK`

## Decision

JSON:
{
  "verdict": "PARK_RISK",
  "issue": {
    "url": "https://github.com/karmonlong/ai-competition-voting-platform/issues/3",
    "title": "Create database schema and models with Supabase",
    "state": "OPEN",
    "labels": [
      "enhancement"
    ],
    "comment_count": 0,
    "updatedAt": "2025-09-05T17:24:16Z"
  },
  "money": true,
  "competition": true,
  "judge": true,
  "local": true,
  "mgfit": true,
  "risk": true
}

## Cheap commands

pwd=/Users/heath/Documents/mathgraph-lean-work/external/money_opportunity_scout_v4_prize_words/karmonlong__ai-competition-voting-platform_3

README head:
# AI竞赛投票平台

一个现代化的AI竞赛投票网站，支持多媒体作品展示、实时投票、炫酷交互效果和完整后台管理功能。

## 🌟 项目特色

- 🎨 **现代化UI设计**: 深色主题 + 渐变效果，支持响应式设计
- 📱 **完全响应式**: 支持桌面/平板/手机多设备访问
- 🎬 **多媒体展示**: 视频、音频、PPT、Word、Web等多种格式支持
- 🗳️ **实时投票系统**: 防刷票机制，实时数据更新
- 🔍 **智能搜索**: 高级搜索和筛选功能
- 📊 **数据可视化**: 实时统计和图表展示
- 💬 **评论互动**: 完整的评论和社交功能
- 🎭 **动画效果**: 流畅的交互动画和过渡效果

## 🏗️ 技术架构

### 前端技术栈
- **框架**: Next.js 14 + React 18 + TypeScript
- **样式**: Tailwind CSS + Framer Motion
- **状态管理**: React Query + Zustand
- **UI组件**: 自定义组件库
- **实时通信**: Socket.io-client

### 后端技术栈
- **数据库**: Supabase (PostgreSQL)
- **认证**: Supabase Auth + JWT
- **文件存储**: Supabase Storage
- **实时功能**: Supabase Realtime
- **ORM**: Prisma

### 部署方案
- **前端**: Vercel (国内访问优化)
- **数据库**: Supabase托管服务
- **CDN**: 自动全球CDN加速

## 🚀 快速开始

### 环境要求
- Node.js 18+
- npm 9+
- Supabase账号

### 安装依赖
```bash
# 使用国内npm镜像
npm config set registry https://registry.npmmirror.com/

# 安装依赖
npm install
```

### 环境配置
1. 复制环境变量文件：
```bash
cp .env.local.example .env.local
```

2. 配置Supabase：
```bash
# 在.env.local中配置您的Supabase项目信息
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 数据库设置
```bash
# 生成Prisma客户端
npm run db:generate

# 推送数据库schema
npm run db:push

# 启动数据库Studio（可选）
npm run db:studio
```

### 开发服务器
```bash
# 启动开发服务器
npm run dev

# 打开浏览器访问 http://localhost:3000
```

## 📁 项目结构

```
ai-competition-voting-platform/
├── src/
│   ├── app/                    # Next.js App Router
│   ├── components/             # React组件
│   ├── lib/                    # 工具函数和配置
│   ├── hooks/                  # 自定义Hooks
│   ├── types/                  # TypeScript类型定义
│   └── utils/                  # 工具函数
├── prisma/                     # 数据库Schema
├── public/                     # 静态资源
├── .claude/                    # 项目管理文件
└── docs/                       # 项目文档
```

## 🎯 开发任务

项目已分解为10个具体任务，详见[.claude/epics/ai-competition-voting-platform/](.claude/epics/ai-competition-voting-platform/)

### 任务概览
1. **基础设施** (001-003): 环境搭建、认证系统、数据库架构
2. **核心功能** (004-007): 文件上传、竞赛管理、投票系统、实时通信
3. **用户体验** (008-010): UI组件、多媒体展示、搜索部署

总工作量：42小时

## 🔧 开发规范

### 代码规范
- 使用TypeScript严格模式
- 遵循ESLint配置
- 使用Prettier格式化代码
- 提交前运行类型检查和测试

### Git工作流
```bash
# 创建功能分支
git checkout -b feature/任务编号-功能描述

# 提交代码
git add .
git commit -m "feat: 任务编号 - 功能描述"

# 推送到远程
git push origin feature/任务编号-功能描述
```

## 🧪 测试

```bash
# 运行所有测试
npm test

# 运行测试并监视文件变化
npm run test:watch

# 生成测试覆盖率报告
npm run test:coverage
```

## 📊 性能优化

- 使用React Query进行数据缓存
- 实现图片懒加载和压缩
- 代码分割和动态导入
- 数据库查询优化
- CDN加速静态资源

## 🔒 安全特性

- JWT认证和授权
- 输入验证和清理
- 文件上传安全检查
- 防刷票机制
- 数据加密存储

## 📈 监控和分析

- 错误日志收集
- 性能监控
- 用户行为分析
- 实时数据监控

## 🚢 部署

### 开发环境
```bash
npm run dev
```

### 生产构建
```bash
npm run build
npm start
```

### 环境变量
确保在生产环境中设置正确的环境变量：
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `DATABASE_URL`

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交您的更改
4. 推送到分支
5. 创建Pull Request

## 📄 许可证

MIT License - 详见[LICENSE](LICENSE)文件

## 🆘 支持

如遇到问题，请：
1. 查看项目文档
2. 在GitHub Issues中搜索类似问题
3. 创建新的Issue描述问题

## 🎉 致谢

感谢所有为这个项目做出贡献的开发者和设计师！

---

**项目状态**: 开发中 ⏳  
**最后更新**: 2025年9月  
**维护团队**: AI竞赛平台开发团队
package scripts:
{
  "dev": "next dev",
  "build": "next build",
  "start": "next start",
  "lint": "next lint",
  "test": "jest",
  "test:watch": "jest --watch",
  "test:coverage": "jest --coverage",
  "db:generate": "prisma generate",
  "db:push": "prisma db push",
  "db:migrate": "prisma migrate dev",
  "db:studio": "prisma studio",
  "db:seed": "node prisma/seed.js",
  "type-check": "tsc --noEmit",
  "format": "prettier --write .",
  "format:check": "prettier --check .",
  "prepare": "husky install"
}


## Issue body

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

## Comments



## Inventory excerpt

top files
.claude/agents/code-analyzer.md
.claude/agents/file-analyzer.md
.claude/agents/parallel-worker.md
.claude/agents/test-runner.md
.claude/CLAUDE.md
.claude/commands/code-rabbit.md
.claude/commands/context/create.md
.claude/commands/context/prime.md
.claude/commands/context/update.md
.claude/commands/pm/blocked.md
.claude/commands/pm/clean.md
.claude/commands/pm/epic-close.md
.claude/commands/pm/epic-decompose.md
.claude/commands/pm/epic-edit.md
.claude/commands/pm/epic-list.md
.claude/commands/pm/epic-merge.md
.claude/commands/pm/epic-oneshot.md
.claude/commands/pm/epic-refresh.md
.claude/commands/pm/epic-show.md
.claude/commands/pm/epic-start-worktree.md
.claude/commands/pm/epic-start.md
.claude/commands/pm/epic-status.md
.claude/commands/pm/epic-sync.md
.claude/commands/pm/help.md
.claude/commands/pm/import.md
.claude/commands/pm/in-progress.md
.claude/commands/pm/init.md
.claude/commands/pm/issue-analyze.md
.claude/commands/pm/issue-close.md
.claude/commands/pm/issue-edit.md
.claude/commands/pm/issue-reopen.md
.claude/commands/pm/issue-show.md
.claude/commands/pm/issue-start.md
.claude/commands/pm/issue-status.md
.claude/commands/pm/issue-sync.md
.claude/commands/pm/next.md
.claude/commands/pm/prd-edit.md
.claude/commands/pm/prd-list.md
.claude/commands/pm/prd-new.md
.claude/commands/pm/prd-parse.md
.claude/commands/pm/prd-status.md
.claude/commands/pm/search.md
.claude/commands/pm/standup.md
.claude/commands/pm/status.md
.claude/commands/pm/sync.md
.claude/commands/pm/test-reference-update.md
.claude/commands/pm/validate.md
.claude/commands/prompt.md
.claude/commands/re-init.md
.claude/commands/testing/prime.md
.claude/commands/testing/run.md
.claude/context/README.md
.claude/epics/.gitkeep
.claude/epics/ai-competition-voting-platform/001.md
.claude/epics/ai-competition-voting-platform/002.md
.claude/epics/ai-competition-voting-platform/003.md
.claude/epics/ai-competition-voting-platform/004.md
.claude/epics/ai-competition-voting-platform/005.md
.claude/epics/ai-competition-voting-platform/006.md
.claude/epics/ai-competition-voting-platform/007.md
.claude/epics/ai-competition-voting-platform/008.md
.claude/epics/ai-competition-voting-platform/009.md
.claude/epics/ai-competition-voting-platform/010.md
.claude/epics/ai-competition-voting-platform/epic.md
.claude/prds/.gitkeep
.claude/prds/ai-competition-voting-platform.md
.claude/rules/agent-coordination.md
.claude/rules/branch-operations.md
.claude/rules/datetime.md
.claude/rules/frontmatter-operations.md
.claude/rules/github-operations.md
.claude/rules/standard-patterns.md
.claude/rules/strip-frontmatter.md
.claude/rules/test-execution.md
.claude/rules/use-ast-grep.md
.claude/rules/worktree-operations.md
.claude/scripts/pm/blocked.sh
.claude/scripts/pm/epic-list.sh
.claude/scripts/pm/epic-show.sh
.claude/scripts/pm/epic-status.sh
.claude/scripts/pm/help.sh
.claude/scripts/pm/in-progress.sh
.claude/scripts/pm/init.sh
.claude/scripts/pm/next.sh
.claude/scripts/pm/prd-list.sh
.claude/scripts/pm/prd-status.sh
.claude/scripts/pm/search.sh
.claude/scripts/pm/standup.sh
.claude/scripts/pm/status.sh
.claude/scripts/pm/validate.sh
.claude/scripts/test-and-log.sh
.claude/settings.local.json
.env.example
.eslintrc.json
.git/config
.git/description
.git/FETCH_HEAD
.git/HEAD
.git/hooks/applypatch-msg.sample
.git/hooks/commit-msg.sample
.git/hooks/fsmonitor-watchman.sample
.git/hooks/post-update.sample
.git/hooks/pre-applypatch.sample
.git/hooks/pre-commit.sample
.git/hooks/pre-merge-commit.sample
.git/hooks/pre-push.sample
.git/hooks/pre-rebase.sample
.git/hooks/pre-receive.sample
.git/hooks/prepare-commit-msg.sample
.git/hooks/push-to-checkout.sample
.git/hooks/update.sample
.git/index
.git/info/exclude
.git/logs/HEAD
.git/objects/pack/pack-9922c2a7f02795699abafbd75a5a3b5ab196831b.idx
.git/objects/pack/pack-9922c2a7f02795699abafbd75a5a3b5ab196831b.pack
.git/objects/pack/pack-9922c2a7f02795699abafbd75a5a3b5ab196831b.promisor
.git/objects/pack/pack-baa79bab03b67811cc6d0a618e93d8eced5cc1b0.idx
.git/objects/pack/pack-baa79bab03b67811cc6d0a618e93d8eced5cc1b0.pack
.git/objects/pack/pack-baa79bab03b67811cc6d0a618e93d8eced5cc1b0.promisor
.git/ORIG_HEAD
.git/packed-refs
.git/refs/heads/main
.gitignore
.npmrc
.prettierrc
CLAUDE.md
DEPLOYMENT.md
DEVELOPMENT.md
jest.config.js
jest.setup.js
next.config.js
package.json
postcss.config.js
prisma/schema.prisma
PROJECT_SUMMARY.md
project-planning.md
QUICK_START.md
README.md
src/app/globals.css
src/app/layout.tsx
src/app/page.tsx
src/components/providers.tsx
src/components/ui/badge.tsx
src/components/ui/button.tsx
src/components/ui/card.tsx
src/lib/prisma.ts
src/lib/supabase-client.ts
src/lib/supabase.ts
src/lib/utils.ts
src/types/supabase.ts
start-dev.sh
tailwind.config.js
tsconfig.json

build/test/competition files
./.claude/agents/code-analyzer.md
./.claude/agents/file-analyzer.md
./.claude/agents/parallel-worker.md
./.claude/agents/test-runner.md
./.claude/CLAUDE.md
./.claude/commands/code-rabbit.md
./.claude/commands/context/create.md
./.claude/commands/context/prime.md
./.claude/commands/context/update.md
./.claude/commands/pm/blocked.md
./.claude/commands/pm/clean.md
./.claude/commands/pm/epic-close.md
./.claude/commands/pm/epic-decompose.md
./.claude/commands/pm/epic-edit.md
./.claude/commands/pm/epic-list.md
./.claude/commands/pm/epic-merge.md
./.claude/commands/pm/epic-oneshot.md
./.claude/commands/pm/epic-refresh.md
./.claude/commands/pm/epic-show.md
./.claude/commands/pm/epic-start-worktree.md
./.claude/commands/pm/epic-start.md
./.claude/commands/pm/epic-status.md
./.claude/commands/pm/epic-sync.md
./.claude/commands/pm/help.md
./.claude/commands/pm/import.md
./.claude/commands/pm/in-progress.md
./.claude/commands/pm/init.md
./.claude/commands/pm/issue-analyze.md
./.claude/commands/pm/issue-close.md
./.claude/commands/pm/issue-edit.md
./.claude/commands/pm/issue-reopen.md
./.claude/commands/pm/issue-show.md
./.claude/commands/pm/issue-start.md
./.claude/commands/pm/issue-status.md
./.claude/commands/pm/issue-sync.md
./.claude/commands/pm/next.md
./.claude/commands/pm/prd-edit.md
./.claude/commands/pm/prd-list.md
./.claude/commands/pm/prd-new.md
./.claude/commands/pm/prd-parse.md
./.claude/commands/pm/prd-status.md
./.claude/commands/pm/search.md
./.claude/commands/pm/standup.md
./.claude/commands/pm/status.md
./.claude/commands/pm/sync.md
./.claude/commands/pm/test-reference-update.md
./.claude/commands/pm/validate.md
./.claude/commands/prompt.md
./.claude/commands/re-init.md
./.claude/commands/testing/prime.md
./.claude/commands/testing/run.md
./.claude/context/README.md
./.claude/epics/ai-competition-voting-platform/001.md
./.claude/epics/ai-competition-voting-platform/002.md
./.claude/epics/ai-competition-voting-platform/003.md
./.claude/epics/ai-competition-voting-platform/004.md
./.claude/epics/ai-competition-voting-platform/005.md
./.claude/epics/ai-competition-voting-platform/006.md
./.claude/epics/ai-competition-voting-platform/007.md
./.claude/epics/ai-competition-voting-platform/008.md
./.claude/epics/ai-competition-voting-platform/009.md
./.claude/epics/ai-competition-voting-platform/010.md
./.claude/epics/ai-competition-voting-platform/epic.md
./.claude/prds/ai-competition-voting-platform.md
./.claude/rules/agent-coordination.md
./.claude/rules/branch-operations.md
./.claude/rules/datetime.md
./.claude/rules/frontmatter-operations.md
./.claude/rules/github-operations.md
./.claude/rules/standard-patterns.md
./.claude/rules/strip-frontmatter.md
./.claude/rules/test-execution.md
./.claude/rules/use-ast-grep.md
./.claude/rules/worktree-operations.md
./CLAUDE.md
./DEPLOYMENT.md
./DEVELOPMENT.md
./package.json
./PROJECT_SUMMARY.md
./project-planning.md
./QUICK_START.md
./README.md

workflows


## Grep excerpt

===== issue body =====
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
===== money/competition/judge hits =====
./PROJECT_SUMMARY.md:48:ai-competition-voting-platform/
./PROJECT_SUMMARY.md:71:│   │   └── 📁 ai-competition-voting-platform/
./PROJECT_SUMMARY.md:75:│       └── 📄 ai-competition-voting-platform.md
./PROJECT_SUMMARY.md:112:git clone https://github.com/karmonlong/ai-competition-voting-platform.git
./PROJECT_SUMMARY.md:113:cd ai-competition-voting-platform
./PROJECT_SUMMARY.md:215:*项目地址: https://github.com/karmonlong/ai-competition-voting-platform*  
./tailwind.config.js:44:          '0%': { opacity: '0' },
./tailwind.config.js:45:          '100%': { opacity: '1' },
./tailwind.config.js:48:          '0%': { transform: 'translateY(10px)', opacity: '0' },
./tailwind.config.js:49:          '100%': { transform: 'translateY(0)', opacity: '1' },
./tailwind.config.js:52:          '0%': { transform: 'scale(0.3)', opacity: '0' },
./tailwind.config.js:55:          '100%': { transform: 'scale(1)', opacity: '1' },
./jest.setup.js:1:// Optional: configure or set up a testing framework before each test.
./jest.setup.js:4:// Used for __tests__/testing-library.js
./jest.setup.js:5:// Learn more: https://github.com/testing-library/jest-dom
./jest.setup.js:6:import '@testing-library/jest-dom'
./jest.config.js:4:  // Provide the path to your Next.js app to load next.config.js and .env files in your test environment
./jest.config.js:11:  testEnvironment: 'jest-environment-jsdom',
./jest.config.js:15:  testMatch: [
./jest.config.js:16:    '**/__tests__/**/*.(ts|tsx|js|jsx)',
./jest.config.js:17:    '**/*.(test|spec).(ts|tsx|js|jsx)',
./jest.config.js:22:    '!src/**/__tests__/**',
./prisma/schema.prisma:29:  submissions       Submission[]
./prisma/schema.prisma:31:  participants      CompetitionParticipant[]
./prisma/schema.prisma:44:  submissionDeadline DateTime
./prisma/schema.prisma:47:  maxParticipants   Int?
./prisma/schema.prisma:49:  prizeDescription  String?
./prisma/schema.prisma:50:  evaluationCriteria Json?
./prisma/schema.prisma:56:  submissions       Submission[]
./prisma/schema.prisma:57:  participants      CompetitionParticipant[]
./prisma/schema.prisma:59:  @@map("competitions")
./prisma/schema.prisma:64:  competitionId     String
./prisma/schema.prisma:65:  participantId     String
./prisma/schema.prisma:71:  submissionData    Json?
./prisma/schema.prisma:76:  competition       Competition @relation(fields: [competitionId], references: [id], onDelete: Cascade)
./prisma/schema.prisma:77:  participant       User @relation(fields: [participantId], references: [id], onDelete: Cascade)
./prisma/schema.prisma:80:  @@unique([competitionId, participantId])
./prisma/schema.prisma:81:  @@map("submissions")
./prisma/schema.prisma:86:  submissionId      String
./prisma/schema.prisma:88:  score             Int
./prisma/schema.prisma:94:  submission        Submission @relation(fields: [submissionId], references: [id], onDelete: Cascade)
./prisma/schema.prisma:97:  @@unique([submissionId, voterId])
./prisma/schema.prisma:101:model CompetitionParticipant {
./prisma/schema.prisma:103:  competitionId     String
./prisma/schema.prisma:106:  status            ParticipantStatus @default(REGISTERED)
./prisma/schema.prisma:108:  competition       Competition @relation(fields: [competitionId], references: [id], onDelete: Cascade)
./prisma/schema.prisma:111:  @@unique([competitionId, userId])
./prisma/schema.prisma:112:  @@map("competition_participants")
./prisma/schema.prisma:152:enum ParticipantStatus {
./.claude/context/README.md:24:- **`tech-context.md`** - Dependencies, technologies, and development tools
./.claude/context/README.md:26:- **`system-patterns.md`** - Architectural patterns and design decisions
./.claude/context/README.md:75:- **Consistent Architecture**: Decisions are documented and followed
./.claude/context/README.md:81:- **Keep Current**: Update context regularly, especially after major changes
./.claude/context/README.md:82:- **Be Concise**: Focus on essential information that helps understanding
./.claude/context/README.md:84:- **Document Decisions**: Capture architectural and design decisions
./.claude/settings.local.json:4:      "Bash(bash .claude/scripts/test-and-log.sh:*)",
./.claude/settings.local.json:5:      "Bash(.claude/scripts/test-and-log.sh:*)",
./.claude/settings.local.json:24:      "Bash(pytest *)",
./.claude/agents/parallel-worker.md:17:- Note dependencies between streams
./.claude/agents/parallel-worker.md:27:    You are implementing a specific work stream in worktree: {worktree_path}
./.claude/agents/parallel-worker.md:36:    3. Commit frequently with format: "Issue #{number}: {specific change}"
./.claude/agents/parallel-worker.md:74:- {combined test results if applicable}
./.claude/agents/parallel-worker.md:93:   - Plan execution order based on dependencies
./.claude/agents/parallel-worker.md:126:1. Note which files are contested
./.claude/agents/parallel-worker.md:151:- Keep the main thread summary extremely concise
./.claude/agents/test-runner.md:2:name: test-runner
./.claude/agents/test-runner.md:3:description: Use this agent when you need to run tests and analyze their results. This agent specializes in executing tests using the optimized test runner script, capturing comprehensive logs, and then performing deep analysis to surface key issues, failures, and actionable insights. The agent should be invoked after code changes that require validation, during debugging sessions when tests are failing, or when you need a comprehensive test health report. Examples: <example>Context: The user wants to run tests after implementing a new feature and understands any issues.user: "I've finished implementing the new authentication flow. Can you run the relevant tests and tell me if there are any problems?" assistant: "I'll use the test-runner agent to run the authentication tests and analyze the results for any issues."<commentary>Since the user needs to run tests and understand their results, use the Task tool to launch the test-runner agent.</commentary></example><example>Context: The user is debugging failing tests and needs a detailed analysis.user: "The workflow tests keep failing intermittently. Can you investigate?" assistant: "Let me use the test-runner agent to run the workflow tests multiple times and analyze the patterns in any failures."<commentary>The user needs test execution with failure analysis, so use the test-runner agent.</commentary></example>
./.claude/agents/test-runner.md:9:You are an expert test execution and analysis specialist for the MUXI Runtime system. Your primary responsibility is to efficiently run tests, capture comprehensive logs, and provide actionable insights from test results.
./.claude/agents/test-runner.md:13:1. **Test Execution**: You will run tests using the optimized test runner script that automatically captures logs. Always use `.claude/scripts/test-and-log.sh` to ensure full output capture.
./.claude/agents/test-runner.md:15:2. **Log Analysis**: After test execution, you will analyze the captured logs to identify:
./.claude/agents/test-runner.md:19:   - Flaky test patterns
./.claude/agents/test-runner.md:21:   - Missing dependencies or setup issues
./.claude/agents/test-runner.md:27:   - **Low**: Minor issues or test infrastructure problems
./.claude/agents/test-runner.md:32:   - Verify test file exists and is executable
./.claude/agents/test-runner.md:34:   - Ensure test dependencies are available
./.claude/agents/test-runner.md:40:   .claude/scripts/test-and-log.sh tests/[test_file].py
./.claude/agents/test-runner.md:42:   # For iteration testing with custom log names
./.claude/agents/test-runner.md:43:   .claude/scripts/test-and-log.sh tests/[test_file].py [test_name]_iteration_[n].log
./.claude/agents/test-runner.md:47:   - Parse the log file for test results summary
./.claude/agents/test-runner.md:50:   - Look for patterns in failures (timing, resources, dependencies)
./.claude/agents/test-runner.md:54:   - Provide a concise summary of test results (passed/failed/skipped)
./.claude/agents/test-runner.md:56:   - Suggest specific fixes or debugging steps
./.claude/agents/test-runner.md:67:- **Import Errors**: Missing modules or circular dependencies
./.claude/agents/test-runner.md:73:Ensure you read the test carefully to understand what it is testing, so you can better analyze the results.
./.claude/agents/test-runner.md:88:[List any blocking issues with specific error messages and line numbers]
./.claude/agents/test-runner.md:101:[Specific actions to fix failures or improve test reliability]
./.claude/agents/test-runner.md:104:## Special Considerations
./.claude/agents/test-runner.md:106:- For flaky tests, suggest running multiple iterations to confirm intermittent behavior
./.claude/agents/test-runner.md:107:- When tests pass but show warnings, highlight these for preventive maintenance
./.claude/agents/test-runner.md:108:- If all tests pass, still check for performance degradation or resource usage patterns
./.claude/agents/test-runner.md:114:If the test runner script fails to execute:
./.claude/agents/test-runner.md:116:2. Verify the test file path is correct
./.claude/agents/test-runner.md:118:4. Fall back to direct pytest execution with output redirection if necessary
./.claude/agents/test-runner.md:120:You will maintain context efficiency by keeping the main conversation focused on actionable insights while ensuring all diagnostic information is captured in the logs for detailed debugging when needed.
./.claude/agents/file-analyzer.md:3:description: Use this agent when you need to analyze and summarize file contents, particularly log files or other verbose outputs, to extract key information and reduce context usage for the parent agent. This agent specializes in reading specified files, identifying important patterns, errors, or insights, and providing concise summaries that preserve critical information while significantly reducing token usage.\n\nExamples:\n- <example>\n  Context: The user wants to analyze a large log file to understand what went wrong during a test run.\n  user: "Please analyze the test.log file and tell me what failed"\n  assistant: "I'll use the file-analyzer agent to read and summarize the log file for you."\n  <commentary>\n  Since the user is asking to analyze a log file, use the Task tool to launch the file-analyzer agent to extract and summarize the key information.\n  </commentary>\n  </example>\n- <example>\n  Context: Multiple files need to be reviewed to understand system behavior.\n  user: "Can you check the debug.log and error.log files from today's run?"\n  assistant: "Let me use the file-analyzer agent to examine both log files and provide you with a summary of the important findings."\n  <commentary>\n  The user needs multiple log files analyzed, so the file-analyzer agent should be used to efficiently extract and summarize the relevant information.\n  </commentary>\n  </example>
./.claude/agents/file-analyzer.md:9:You are an expert file analyzer specializing in extracting and summarizing critical information from files, particularly log files and verbose outputs. Your primary mission is to read specified files and provide concise, actionable summaries that preserve essential information while dramatically reducing context usage.
./.claude/agents/file-analyzer.md:14:   - Read the exact files specified by the user or parent agent
./.claude/agents/file-analyzer.md:15:   - Never assume which files to read - only analyze what was explicitly requested
./.claude/agents/file-analyzer.md:24:     * Performance metrics and timestamps
./.claude/agents/file-analyzer.md:46:   - Use concise language without sacrificing clarity
./.claude/agents/file-analyzer.md:56:   - [Most important issues/errors with specific details]
./.claude/agents/file-analyzer.md:57:   - [Include exact error messages when crucial]
./.claude/agents/file-analyzer.md:67:6. **Special Handling**
./.claude/agents/file-analyzer.md:68:   - For test logs: Focus on test results, failures, and assertion errors
./.claude/agents/file-analyzer.md:83:- If files are already concise, indicate this rather than padding the summary
./.claude/agents/file-analyzer.md:85:- Always preserve specific error codes, line numbers, and identifiers that might be needed for debugging
./.claude/agents/file-analyzer.md:87:Your summaries enable efficient decision-making by distilling large amounts of information into actionable insights while maintaining complete accuracy on critical details.
./.claude/agents/code-analyzer.md:3:description: Use this agent when you need to analyze code changes for potential bugs, trace logic flow across multiple files, or investigate suspicious behavior in the codebase. This agent specializes in deep-dive analysis while maintaining a concise summary format to preserve context. Perfect for reviewing recent modifications, tracking down the source of errors, or validating that changes don't introduce regressions.\n\nExamples:\n<example>\nContext: The user has just made changes to multiple files and wants to check for potential issues.\nuser: "I've updated the authentication flow across several files. Can you check for bugs?"\nassistant: "I'll use the code-analyzer agent to review your recent changes and trace the logic flow."\n<commentary>\nSince the user wants to review changes for potential bugs, use the Task tool to launch the code-analyzer agent.\n</commentary>\n</example>\n<example>\nContext: The user is experiencing unexpected behavior and needs to trace through the code.\nuser: "The API is returning 500 errors after the last deployment. Need to find what's broken."\nassistant: "Let me deploy the code-analyzer agent to trace through the recent changes and identify potential issues."\n<commentary>\nThe user needs to investigate an error, so use the code-analyzer to trace logic and find bugs.\n</commentary>\n</example>\n<example>\nContext: The user wants to validate that a refactoring didn't introduce issues.\nuser: "I refactored the database connection pooling. Check if I broke anything."\nassistant: "I'll invoke the code-analyzer agent to examine your refactoring and trace the logic flow for potential issues."\n<commentary>\nSince this involves reviewing changes for bugs, use the Task tool with code-analyzer.\n</commentary>\n</example>
./.claude/agents/code-analyzer.md:9:You are an elite bug hunting specialist with deep expertise in code analysis, logic tracing, and vulnerability detection. Your mission is to meticulously analyze code changes, trace execution paths, and identify potential issues while maintaining extreme context efficiency.
./.claude/agents/code-analyzer.md:13:1. **Change Analysis**: Review modifications in files with surgical precision, focusing on:
./.claude/agents/code-analyzer.md:17:   - Inconsistencies between related changes
./.claude/agents/code-analyzer.md:19:2. **Logic Tracing**: Follow execution paths across files to:
./.claude/agents/code-analyzer.md:22:   - Detect circular dependencies or infinite loops
./.claude/agents/code-analyzer.md:30:   - Type mismatches and implicit conversions
./.claude/agents/code-analyzer.md:38:4. **Cross-Reference**: Check for inconsistencies across related files
./.claude/agents/code-analyzer.md:39:5. **Synthesize**: Create concise, actionable findings
./.claude/agents/code-analyzer.md:65:[Concise flow diagram or key path description]
./.claude/agents/code-analyzer.md:71:**Operating Principles:**
./.claude/agents/code-analyzer.md:73:- **Context Preservation**: Use extremely concise language. Every word must earn its place.
./.claude/agents/code-anal

