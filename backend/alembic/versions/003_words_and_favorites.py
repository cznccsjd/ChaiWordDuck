"""Add words, query_logs and favorites tables

Revision ID: 003_words_and_favorites
Revises: 002_fix_schema
Create Date: 2025-10-15 14:00:00.000000

Adds core business tables:
- words: Store word definitions and decomposition data
- query_logs: Track user queries for rate limiting
- favorites: Store user favorites
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003_words_and_favorites'
down_revision: Union[str, None] = '002_fix_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create words, query_logs and favorites tables"""

    # 1. Create words table
    op.create_table(
        'words',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('word', sa.String(length=100), nullable=False),
        sa.Column('phonetic', sa.String(length=50), nullable=True),
        sa.Column('part_of_speech', sa.String(length=20), nullable=True),
        sa.Column('core_game', sa.Text(), nullable=False),
        sa.Column('scenario_formal', sa.Text(), nullable=False),
        sa.Column('scenario_casual', sa.Text(), nullable=False),
        sa.Column('etymology_breakdown', sa.Text(), nullable=False),
        sa.Column('etymology_story', sa.Text(), nullable=True),
        sa.Column('common_mistakes', sa.Text(), nullable=False),
        sa.Column('memory_trick', sa.Text(), nullable=False),
        sa.Column('is_golden', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('source', sa.String(length=20), nullable=False, server_default='ai'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint("source IN ('ai', 'manual')", name='check_word_source')
    )

    # Create indexes for words
    op.create_index('idx_words_word', 'words', ['word'], unique=True)
    op.create_index('idx_words_is_golden', 'words', ['is_golden'])

    # 2. Create query_logs table
    op.create_table(
        'query_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('guest_session_id', sa.String(length=36), nullable=True),
        sa.Column('word_id', sa.Integer(), nullable=False),
        sa.Column('query_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['guest_session_id'], ['guest_sessions.guest_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['word_id'], ['words.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint(
            '(user_id IS NOT NULL AND guest_session_id IS NULL) OR (user_id IS NULL AND guest_session_id IS NOT NULL)',
            name='check_query_log_owner'
        )
    )

    # Create indexes for query_logs
    op.create_index('idx_query_logs_user_date', 'query_logs', ['user_id', 'query_date'])
    op.create_index('idx_query_logs_guest_date', 'query_logs', ['guest_session_id', 'query_date'])
    op.create_index('idx_query_logs_word', 'query_logs', ['word_id'])

    # 3. Create favorites table
    op.create_table(
        'favorites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('word_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['word_id'], ['words.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'word_id', name='uq_user_word_favorite')
    )

    # Create indexes for favorites
    op.create_index('idx_favorites_user', 'favorites', ['user_id'])
    op.create_index('idx_favorites_created', 'favorites', ['created_at'], postgresql_ops={'created_at': 'DESC'})

    # 4. Insert golden handbook words (MVP预置数据)
    op.execute("""
        INSERT INTO words (word, phonetic, part_of_speech, core_game, scenario_formal, scenario_casual,
                          etymology_breakdown, etymology_story, common_mistakes, memory_trick, is_golden, source)
        VALUES
        ('accommodation', '/əˌkɑːməˈdeɪʃn/', 'noun',
         '这是一场"双向调整以达成共处"的协商游戏',
         '商务谈判中的妥协调和：双方都要做出调整来达成合作',
         '旅行中的住宿：酒店为客人提供舒适的休息场所',
         'ac-(to, 朝向) + commod-(convenient, 方便) + -ation(名词后缀)',
         '古罗马时代，主人为了让客人住得舒服，会调整房间布置和自己的习惯。这种"双向调整达成舒适共处"的理念，演变成了accommodation这个词。',
         '最容易犯的错：拼写时漏掉一个m或一个c。正确拼写记住：两个c，两个m',
         '想象酒店房间有两张床(cc)和两个枕头(mm)，这样就记住了accommodation的拼写',
         1, 'manual'),

        ('embarrassment', '/ɪmˈbærəsmənt/', 'noun',
         '这是一种"被公众关注而手足无措"的社交困境游戏',
         '演讲时忘词，全场目光聚焦，内心尴尬万分',
         '约会时裤子突然开线，瞬间脸红心跳',
         'em-(into, 进入) + barr-(bar, 障碍) + -ass- + -ment(名词后缀)',
         '词源来自法语embarrasser，原意是"被栅栏围住，进退两难"。就像被困在众人目光的栅栏中，想逃逃不掉的尴尬处境。',
         '拼写陷阱：两个r，两个s。很多人会漏掉一个',
         '记住em-BARR(两个r)-ASS(两个s)-ment，想象尴尬时"屁股(ass)被栅栏(barr)卡住"',
         1, 'manual'),

        ('procrastination', '/proʊˌkræstɪˈneɪʃn/', 'noun',
         '这是一场"明日复明日"的自我欺骗游戏',
         '项目截止日期临近，却还在刷社交媒体',
         '想健身却总说"明天开始"，结果一拖再拖',
         'pro-(forward, 向前) + crastin-(tomorrow, 明天) + -ation(名词后缀)',
         '拉丁语crastinus意为"属于明天的"。把今天的事推到明天，明天的事推到后天，这就是procrastination的本质。',
         '容易拼错的部分：中间的-crastin-，记住包含"cras"（明天）',
         '谐音记忆："拖-cras-ti-nation" = "拖到明天"的国度',
         1, 'manual'),

        ('Mediterranean', '/ˌmedɪtəˈreɪniən/', 'adjective',
         '这是"陆地中间的海"的地理命名游戏',
         '地中海气候区的农业特征研究',
         '去地中海度假，享受阳光沙滩和美食',
         'medi-(middle, 中间) + terr-(land, 陆地) + -anean(形容词后缀)',
         '地中海被欧洲、亚洲和非洲三大陆包围，是真正的"陆地中间的海"，因此得名Mediterranean。',
         '易错点：中间的-rr-要双写，-anean结尾容易拼错',
         '拆解记忆：medi(中间) + terr(陆地) + anean → 陆地中间的海',
         1, 'manual'),

        ('Massachusetts', '/ˌmæsəˈtʃuːsɪts/', 'noun',
         '这是印第安部落名称演变的历史游戏',
         '美国马萨诸塞州的历史文化研究',
         'MIT和哈佛都在Massachusetts，教育重镇',
         'Massa-(great, 大的) + chusetts(hills, 山丘)',
         '源自印第安语Massachusett部落，意为"大山丘附近的地方"。欧洲殖民者保留了这个印第安地名，演变成今天的州名。',
         '超级易错：两个s，两个t，中间还有chu。是美国最难拼的州名之一',
         '分段记忆：Massa + chu + setts，想象"麻辣(Ma-ssa)猪(chu)蹄(setts)"',
         1, 'manual'),

        ('entrepreneur', '/ˌɑːntrəprəˈnɜːr/', 'noun',
         '这是一场"承担风险追求机会"的商业冒险游戏',
         '风险投资家评估创业者的商业计划',
         '辞掉工作，创办自己的咖啡店，成为entrepreneur',
         'entre-(between, 之间) + prendre(to take, 拿取) + -eur(人)',
         '法语词根，原意是"在机会之间穿梭并抓住它的人"。企业家就是那些敢于在不确定性中抓住商机的人。',
         '易错：中间的-pre-，结尾的-eur。很多人会拼成-or',
         '谐音：按-tre-pre-neur，"安特儿-扑-呢儿"',
         1, 'manual'),

        ('conscientious', '/ˌkɑːnʃiˈenʃəs/', 'adjective',
         '这是"良心驱动的细致负责"品质游戏',
         '他是个conscientious的会计师，每笔账目都仔细核对',
         '室友特别conscientious，总是主动打扫卫生',
         'con-(together, 一起) + sci-(know, 知道) + -entious(形容词后缀)',
         '词根sci-表示"知道"，conscience是"良心"。conscientious就是"有良心地做事"，引申为认真负责。',
         '拼写难点：-sci-和-enti-的组合，中间的t容易漏',
         '联想记忆：con + science(科学) + tious → 像科学家一样严谨认真',
         1, 'manual'),

        ('pharmaceutical', '/ˌfɑːrməˈsuːtɪkl/', 'adjective',
         '这是"药物制造与应用"的医学科技游戏',
         '大型pharmaceutical公司研发新冠疫苗',
         '药店里pharmaceutical产品琳琅满目',
         'pharmac-(drug, 药物) + -eutic-(relating to, 相关的) + -al(形容词后缀)',
         '希腊语pharmakon原意是"药物、毒药"。古代医学中，药和毒往往只是剂量之差。',
         '易错：ph-开头(不是f)，中间-ceu-组合特殊',
         '拆解：pharm(药房) +aceutical，想象药房里的专业药品',
         1, 'manual'),

        ('archaeology', '/ˌɑːrkiˈɑːlədʒi/', 'noun',
         '这是"挖掘古代遗迹探索历史"的时光穿越游戏',
         '考古学家通过archaeology发现古埃及文明',
         '看纪录片学archaeology，了解恐龙化石挖掘过程',
         'archae-(ancient, 古代的) + -ology(study, 学科)',
         '希腊语archaios意为"古老的"。考古学就是研究古老事物的学科。',
         '英美拼写差异：美式archaeology，英式archeology(少一个a)',
         '记忆：arch(拱门，古建筑) + ae + ology(学科) → 研究古建筑的学科',
         1, 'manual'),

        ('bureaucracy', '/bjʊˈrɑːkrəsi/', 'noun',
         '这是"办公桌统治"的权力运作游戏',
         '政府机构的bureaucracy导致审批流程繁琐',
         '办个证件跑了五个部门，被bureaucracy折磨惨了',
         'bureau-(office, 办公室) + -cracy(rule, 统治)',
         '法语bureau原意是"办公桌"。bureaucracy直译就是"办公桌的统治"，指依靠文书和流程运转的官僚体系。',
         '拼写难点：bureau-部分，-cracy结尾(不是-crazy)',
         '联想：bureau(局) + cracy(统治) → 官僚局的统治方式',
         1, 'manual')
    """)


def downgrade() -> None:
    """Drop words, query_logs and favorites tables"""

    # Drop favorites table
    op.drop_index('idx_favorites_created', table_name='favorites')
    op.drop_index('idx_favorites_user', table_name='favorites')
    op.drop_table('favorites')

    # Drop query_logs table
    op.drop_index('idx_query_logs_word', table_name='query_logs')
    op.drop_index('idx_query_logs_guest_date', table_name='query_logs')
    op.drop_index('idx_query_logs_user_date', table_name='query_logs')
    op.drop_table('query_logs')

    # Drop words table
    op.drop_index('idx_words_is_golden', table_name='words')
    op.drop_index('idx_words_word', table_name='words')
    op.drop_table('words')
