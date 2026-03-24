import sqlite3
import hashlib
from werkzeug.security import generate_password_hash
import os
import sys


def init_database():
    if not os.path.exists('instance'):
        os.makedirs('instance')
    print("=== INITIALIZING DATABASE ===")
    conn = sqlite3.connect('instance/app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("Creating users table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        display_name TEXT,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user',
        is_banned BOOLEAN DEFAULT 0,
        ban_reason TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        karma INTEGER DEFAULT 0,
        bio TEXT DEFAULT '',
        avatar_color TEXT DEFAULT '#e8402a'
    )
    ''')

    print("Creating communities table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS communities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        description TEXT,
        owner_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        subscribers_count INTEGER DEFAULT 0,
        is_public BOOLEAN DEFAULT 1,
        FOREIGN KEY (owner_id) REFERENCES users (id)
    )
    ''')

    print("Creating community_subscriptions table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS community_subscriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        community_id INTEGER NOT NULL,
        subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, community_id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (community_id) REFERENCES communities (id)
    )
    ''')

    print("Creating posts table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        community_id INTEGER,
        post_type TEXT DEFAULT 'text',
        upvotes INTEGER DEFAULT 0,
        downvotes INTEGER DEFAULT 0,
        comments_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_deleted BOOLEAN DEFAULT 0,
        deleted_by INTEGER,
        deleted_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (community_id) REFERENCES communities (id),
        FOREIGN KEY (deleted_by) REFERENCES users (id)
    )
    ''')

    print("Creating comments table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        content TEXT NOT NULL,
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        parent_id INTEGER,
        upvotes INTEGER DEFAULT 0,
        downvotes INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_deleted BOOLEAN DEFAULT 0,
        deleted_by INTEGER,
        deleted_at TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (post_id) REFERENCES posts (id),
        FOREIGN KEY (parent_id) REFERENCES comments (id),
        FOREIGN KEY (deleted_by) REFERENCES users (id)
    )
    ''')

    print("Creating votes table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        vote_type TEXT NOT NULL,
        UNIQUE(user_id, post_id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (post_id) REFERENCES posts (id)
    )
    ''')

    print("Creating comment_votes table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS comment_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        comment_id INTEGER NOT NULL,
        vote_type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, comment_id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (comment_id) REFERENCES comments (id)
    )
    ''')

    print("Creating bookmarks table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bookmarks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        post_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, post_id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (post_id) REFERENCES posts (id)
    )
    ''')

    print("Creating reports table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_id INTEGER NOT NULL,
        content_type TEXT NOT NULL,
        content_id INTEGER NOT NULL,
        reason TEXT NOT NULL,
        description TEXT,
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviewed_by INTEGER,
        reviewed_at TIMESTAMP,
        FOREIGN KEY (reporter_id) REFERENCES users (id),
        FOREIGN KEY (reviewed_by) REFERENCES users (id)
    )
    ''')

    print("Creating user_bans table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_bans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        banned_by INTEGER NOT NULL,
        reason TEXT,
        banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        expires_at TIMESTAMP,
        UNIQUE(user_id),
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (banned_by) REFERENCES users (id)
    )
    ''')

    print("Creating moderation_logs table...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS moderation_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        moderator_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        target_type TEXT NOT NULL,
        target_id INTEGER,
        details TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (moderator_id) REFERENCES users (id)
    )
    ''')

    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        print("Creating admin and moderator...")
        admin_hash = generate_password_hash('admin123')
        cursor.execute(
            "INSERT INTO users (username, display_name, email, password_hash, role, karma, bio, avatar_color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ('admin', 'Administrator', 'admin@example.com', admin_hash, 'admin', 150, 'Главный администратор платформы Rebu', '#e8402a')
        )
        admin_id = cursor.lastrowid
        print(f"Admin created with ID: {admin_id} (login: admin, password: admin123)")

        mod_hash = generate_password_hash('mod123')
        cursor.execute(
            "INSERT INTO users (username, display_name, email, password_hash, role, karma, bio, avatar_color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ('moderator', 'Moderator', 'mod@example.com', mod_hash, 'moderator', 85, 'Модератор сообществ, слежу за порядком', '#2563eb')
        )
        mod_id = cursor.lastrowid
        print(f"Moderator created with ID: {mod_id} (login: moderator, password: mod123)")

        # Создаем дополнительных пользователей
        user_hash = generate_password_hash('user123')
        cursor.execute(
            "INSERT INTO users (username, display_name, email, password_hash, role, karma, bio, avatar_color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ('alex', 'Алексей Смирнов', 'alex@example.com', user_hash, 'user', 42, 'Люблю технологии и программирование', '#16a34a')
        )
        alex_id = cursor.lastrowid
        print(f"User alex created with ID: {alex_id}")

        cursor.execute(
            "INSERT INTO users (username, display_name, email, password_hash, role, karma, bio, avatar_color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ('maria', 'Мария Петрова', 'maria@example.com', user_hash, 'user', 78, 'Фотограф и путешественница', '#d97706')
        )
        maria_id = cursor.lastrowid
        print(f"User maria created with ID: {maria_id}")

        cursor.execute(
            "INSERT INTO users (username, display_name, email, password_hash, role, karma, bio, avatar_color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ('dmitry', 'Дмитрий Козлов', 'dmitry@example.com', user_hash, 'user', 23, 'Начинающий разработчик', '#9333ea')
        )
        dmitry_id = cursor.lastrowid
        print(f"User dmitry created with ID: {dmitry_id}")

        # 4 сообщества
        communities = [
            ('tech', 'Технологии и IT', 'Всё о технологиях, программировании, гаджетах и IT-новостях', admin_id),
            ('photography', 'Фотография', 'Обсуждаем фотографию, делимся работами и советами', admin_id),
            ('movies', 'Кино и сериалы', 'Обсуждение фильмов, сериалов и киноновинок', mod_id),
            ('gaming', 'Игровая', 'Видеоигры, новости игровой индустрии и обсуждения', admin_id)
        ]

        community_ids = {}
        for name, display_name, description, owner_id in communities:
            cursor.execute(
                "INSERT INTO communities (name, display_name, description, owner_id) VALUES (?, ?, ?, ?)",
                (name, display_name, description, owner_id)
            )
            community_ids[name] = cursor.lastrowid
            print(f"Community r/{name} created with ID: {community_ids[name]}")

        # Подписки на сообщества
        subscriptions = [
            (admin_id, community_ids['tech']),
            (admin_id, community_ids['movies']),
            (mod_id, community_ids['tech']),
            (mod_id, community_ids['gaming']),
            (alex_id, community_ids['tech']),
            (alex_id, community_ids['gaming']),
            (maria_id, community_ids['photography']),
            (maria_id, community_ids['movies']),
            (dmitry_id, community_ids['tech']),
            (dmitry_id, community_ids['gaming']),
        ]

        for user_id, community_id in subscriptions:
            cursor.execute(
                "INSERT INTO community_subscriptions (user_id, community_id) VALUES (?, ?)",
                (user_id, community_id)
            )
            cursor.execute(
                "UPDATE communities SET subscribers_count = subscribers_count + 1 WHERE id = ?",
                (community_id,)
            )

        # 10 постов с контентом
        posts_data = [
            # Сообщество tech
            (admin_id, community_ids['tech'], 'Что нового в Python 3.13?',
             '<p>Python 3.13 приносит много интересных улучшений:</p><ul><li>Улучшенная производительность интерпретатора</li><li>Новые возможности для асинхронного программирования</li><li>Улучшенная обработка ошибок</li><li>Экспериментальная поддержка JIT-компиляции</li></ul><p>Какие фичи вам больше всего понравились?</p>', 12, 3, 5),
            (alex_id, community_ids['tech'], 'Как я перешел с Windows на Linux',
             '<p>После 10 лет использования Windows я наконец решился перейти на Linux (Ubuntu).</p><p><strong>Плюсы:</strong> скорость работы, отсутствие рекламы, полный контроль над системой.</p><p><strong>Минусы:</strong> некоторый софт пришлось искать аналоги.</p><p>Поделитесь своим опытом перехода!</p>', 8, 2, 4),
            (dmitry_id, community_ids['tech'], 'React vs Vue: что выбрать в 2026?',
             '<p>Оба фреймворка активно развиваются. React имеет большую экосистему, Vue проще для изучения.</p><p>Что вы предпочитаете и почему?</p>', 15, 5, 8),

            # Сообщество photography
            (maria_id, community_ids['photography'], 'Мои лучшие фотографии осени 2025',
             '<p>Вот несколько кадров, которые мне особенно удались в прошлом году:</p><p>Использовал камеру Sony A7IV с объективом 85mm f/1.8.</p><p>Жду ваших отзывов и советов!</p>', 25, 2, 12),
            (admin_id, community_ids['photography'], 'Советы для начинающих фотографов',
             '<p>Вот несколько важных советов:</p><ul><li>Всегда носите камеру с собой</li><li>Учитесь работать с естественным светом</li><li>Не бойтесь экспериментировать</li><li>Изучайте работы известных фотографов</li></ul><p>Какие советы вы бы добавили?</p>', 18, 1, 9),
            (maria_id, community_ids['photography'], 'Обзор объектива 50mm f/1.8',
             '<p>Самый доступный светосильный объектив. Отлично подходит для портретов и уличной фотографии.</p><p>Цена/качество - идеально для новичков.</p><p>У кого есть этот объектив? Делитесь фотографиями!</p>', 10, 1, 6),

            # Сообщество movies
            (mod_id, community_ids['movies'], '10 лучших фильмов 2025 года',
             '<p>Мой личный топ:</p><ol><li>Дюна: Часть вторая</li><li>Оппенгеймер</li><li>Барби</li><li>Бедные-несчастные</li><li>Мастер</li><li>Субстанция</li><li>Фуриоса</li><li>Ворон</li><li>Смерч 2</li><li>Гладиатор 2</li></ol><p>Согласны? Что добавили бы в этот список?</p>', 35, 4, 15),
            (maria_id, community_ids['movies'], 'Сериалы, которые стоит посмотреть',
             '<p>За последний год особенно впечатлили:</p><ul><li>Медленные лошади (Apple TV+)</li><li>Сёгун (FX/Hulu)</li><li>Фоллаут (Amazon)</li><li>Рипли (Netflix)</li></ul><p>Ваши рекомендации?</p>', 22, 3, 11),
            (alex_id, community_ids['movies'], 'Почему "Интерстеллар" остается лучшим научно-фантастическим фильмом',
             '<p>Спустя 11 лет после выхода "Интерстеллар" всё ещё остаётся эталоном научной фантастики.</p><p>Нолан создал не просто фильм, а настоящее путешествие через время и пространство.</p><p>Что вы думаете о фильме? Какой ваш любимый момент?</p>', 45, 2, 18),

            # Сообщество gaming
            (admin_id, community_ids['gaming'], 'Лучшие игры 2025: первые впечатления',
             '<p>В этом году вышло много отличных игр:</p><ul><li>Elden Ring: Shadow of the Erdtree</li><li>Final Fantasy VII Rebirth</li><li>Like a Dragon: Infinite Wealth</li><li>Helldivers 2</li><li>Black Myth: Wukong</li></ul><p>Во что играете сейчас?</p>', 28, 6, 14),
            (dmitry_id, community_ids['gaming'], 'Почему я люблю инди-игры',
             '<p>Инди-игры часто предлагают уникальные механики и свежие идеи, которые не найти в AAA-проектах.</p><p>Мои фавориты: Hollow Knight, Stardew Valley, Hades, Celeste.</p><p>Какие инди-игры вы бы порекомендовали?</p>', 12, 2, 7)
        ]

        post_ids = []
        for user_id, community_id, title, content, upvotes, downvotes, comments_count in posts_data:
            cursor.execute('''
                INSERT INTO posts (title, content, user_id, community_id, upvotes, downvotes, comments_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now', '-1 day', '+' || ? || ' hours'))
            ''', (title, content, user_id, community_id, upvotes, downvotes, comments_count, len(post_ids) * 2))
            post_ids.append(cursor.lastrowid)

        print(f"Created {len(post_ids)} posts")

        # Комментарии к постам
        comments_data = [
            # Комментарии к первому посту (Python 3.13)
            (mod_id, post_ids[0], None, 'Отличные новости! Особенно жду улучшения асинхронности.'),
            (alex_id, post_ids[0], None, 'JIT-компиляция звучит очень интересно. Надеюсь, в следующей версии будет стабильно.'),
            (dmitry_id, post_ids[0], None, 'Python становится всё быстрее, это радует!'),

            # Комментарии ко второму посту (Linux)
            (mod_id, post_ids[1], None, 'Добро пожаловать в мир Linux! Рекомендую попробовать Arch, если хочется больше контроля.'),
            (admin_id, post_ids[1], None, 'Ubuntu - отличный выбор для начала. Со временем можно перейти на что-то более продвинутое.'),
            (maria_id, post_ids[1], None, 'Я тоже перешла на Linux для работы с фото. GIMP и Darktable работают отлично!'),

            # Комментарии к третьему посту (React vs Vue)
            (admin_id, post_ids[2], None, 'React для крупных проектов, Vue для быстрых прототипов. Оба хороши.'),
            (mod_id, post_ids[2], None, 'Vue проще в изучении, но React даёт больше вакансий на рынке.'),
            (alex_id, post_ids[2], None, 'Использую оба. React для работы, Vue для личных проектов.'),

            # Комментарии к посту о фотографиях
            (admin_id, post_ids[3], None, 'Красивые кадры! Особенно понравилась третья фотография.'),
            (dmitry_id, post_ids[3], None, 'Отличная работа! На какой объектив снимали?'),
            (mod_id, post_ids[3], None, 'Прекрасная цветопередача. Как обрабатывали?'),

            # Комментарии к советам для фотографов
            (maria_id, post_ids[4], None, 'Совет: всегда снимайте в RAW, это даёт больше возможностей при обработке.'),
            (alex_id, post_ids[4], None, 'Главное - практика. Чем больше снимаете, тем быстрее прогресс.'),
            (dmitry_id, post_ids[4], None, 'Спасибо за советы, очень полезно для новичка!'),

            # Комментарии к обзору объектива
            (admin_id, post_ids[5], None, 'Классика. Этот объектив должен быть у каждого фотографа.'),
            (mod_id, post_ids[5], None, 'Согласен, отличный выбор для старта.'),
            (alex_id, post_ids[5], None, 'Тоже пользуюсь, очень доволен качеством.'),

            # Комментарии к топу фильмов
            (admin_id, post_ids[6], None, 'Дюна - однозначно лучший фильм года. Вильнёв гений.'),
            (maria_id, post_ids[6], None, 'Оппенгеймер тоже очень сильный. Нолан вновь на высоте.'),
            (dmitry_id, post_ids[6], None, 'Барби был неожиданно хорош!'),

            # Комментарии к сериалам
            (mod_id, post_ids[7], None, 'Сёгун - шедевр. Лучший сериал года по версии многих критиков.'),
            (admin_id, post_ids[7], None, 'Фоллаут приятно удивил. Жду второй сезон.'),
            (maria_id, post_ids[7], None, 'Добавьте "Медвежонок" в список, тоже отличный сериал!'),

            # Комментарии к Интерстеллару
            (admin_id, post_ids[8], None, 'Сцена с док-станцией и матч-кат - одна из лучших в истории кино.'),
            (mod_id, post_ids[8], None, 'Ханс Циммер создал гениальный саундтрек. Без него фильм был бы другим.'),
            (maria_id, post_ids[8], None, 'Каждый раз пересматриваю и нахожу что-то новое.'),
            (dmitry_id, post_ids[8], None, 'Согласен на 100%. Лучший sci-fi фильм.'),

            # Комментарии к лучшим играм
            (mod_id, post_ids[9], None, 'Shadow of the Erdtree - дополнение года. FromSoftware снова на высоте.'),
            (alex_id, post_ids[9], None, 'Helldivers 2 - отличная кооперативная игра, провёл уже 100 часов.'),
            (maria_id, post_ids[9], None, 'Black Myth Wukong выглядит потрясающе. Жду выхода.'),

            # Комментарии к инди-играм
            (admin_id, post_ids[10], None, 'Hollow Knight - шедевр. Жду Silksong с нетерпением.'),
            (mod_id, post_ids[10], None, 'Hades - лучший roguelike. Супергиант проделали отличную работу.'),
            (alex_id, post_ids[10], None, 'Stardew Valley - антистресс. Идеально после работы.')
        ]

        for user_id, post_id, parent_id, content in comments_data:
            cursor.execute('''
                INSERT INTO comments (content, user_id, post_id, parent_id, upvotes, downvotes)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (content, user_id, post_id, parent_id, 2, 0))
            comment_id = cursor.lastrowid

            # Добавляем немного голосов к некоторым комментариям
            if parent_id is None:
                cursor.execute('UPDATE posts SET comments_count = comments_count + 1 WHERE id = ?', (post_id,))

        print(f"Created comments")

        # Обновляем карму пользователей
        cursor.execute('UPDATE users SET karma = 150 WHERE id = ?', (admin_id,))
        cursor.execute('UPDATE users SET karma = 85 WHERE id = ?', (mod_id,))
        cursor.execute('UPDATE users SET karma = 42 WHERE id = ?', (alex_id,))
        cursor.execute('UPDATE users SET karma = 78 WHERE id = ?', (maria_id,))
        cursor.execute('UPDATE users SET karma = 23 WHERE id = ?', (dmitry_id,))

        conn.commit()
        print("All test data created successfully!")

    conn.commit()

    print("\n=== DATABASE CHECK ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables created: {[t[0] for t in tables]}")
    cursor.execute("SELECT id, username, display_name, role FROM users")
    users = cursor.fetchall()
    print(f"\nUsers in database:")
    for user in users:
        print(f"  ID: {user[0]}, Username: {user[1]}, Display Name: {user[2]}, Role: {user[3]}")
    cursor.execute("SELECT COUNT(*) FROM communities")
    communities = cursor.fetchone()[0]
    print(f"\nCommunities in database: {communities}")
    cursor.execute("SELECT COUNT(*) FROM posts")
    posts = cursor.fetchone()[0]
    print(f"Posts in database: {posts}")
    cursor.execute("SELECT COUNT(*) FROM comments")
    comments = cursor.fetchone()[0]
    print(f"Comments in database: {comments}")
    cursor.execute("SELECT COUNT(*) FROM reports WHERE status='pending'")
    pending_reports = cursor.fetchone()[0]
    print(f"Pending reports: {pending_reports}")
    conn.close()
    print("\n=== DATABASE INITIALIZATION COMPLETE ===")
    print("Test credentials:")
    print("  Admin: admin / admin123")
    print("  Moderator: moderator / mod123")
    print("  Regular users: alex / user123, maria / user123, dmitry / user123")
    print("\nCommunities created:")
    print("  r/tech - Технологии и IT")
    print("  r/photography - Фотография")
    print("  r/movies - Кино и сериалы")
    print("  r/gaming - Игровая")
    print("\nTotal posts created: 11 (10 main + existing welcome post)")


def update_database():
    print("=== UPDATING DATABASE ===")
    conn = sqlite3.connect('instance/app.db')
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    try:
        # Добавляем display_name в users
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN display_name TEXT")
            print("Added column display_name to users table")
            cursor.execute("UPDATE users SET display_name = username WHERE display_name IS NULL")
            conn.commit()
        except:
            pass

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN bio TEXT DEFAULT ''")
            print("Added column bio to users table")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_color TEXT DEFAULT '#e8402a'")
            print("Added column avatar_color to users table")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
            print("Added column role to users table")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN is_banned BOOLEAN DEFAULT 0")
            print("Added column is_banned to users table")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE users ADD COLUMN ban_reason TEXT")
            print("Added column ban_reason to users table")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE posts ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
            print("Added column is_deleted to posts table")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE posts ADD COLUMN deleted_by INTEGER REFERENCES users(id)")
            print("Added column deleted_by to posts table")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE posts ADD COLUMN deleted_at TIMESTAMP")
            print("Added column deleted_at to posts table")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE comments ADD COLUMN is_deleted BOOLEAN DEFAULT 0")
            print("Added column is_deleted to comments table")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE comments ADD COLUMN deleted_by INTEGER REFERENCES users(id)")
            print("Added column deleted_by to comments table")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE comments ADD COLUMN deleted_at TIMESTAMP")
            print("Added column deleted_at to comments table")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE comments ADD COLUMN parent_id INTEGER REFERENCES comments(id)")
            print("Added column parent_id to comments table")
        except:
            pass

        try:
            cursor.execute("ALTER TABLE comments ADD COLUMN upvotes INTEGER DEFAULT 0")
            cursor.execute("ALTER TABLE comments ADD COLUMN downvotes INTEGER DEFAULT 0")
            print("Added upvotes/downvotes to comments table")
        except:
            pass

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS comment_votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            comment_id INTEGER NOT NULL,
            vote_type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, comment_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (comment_id) REFERENCES comments (id)
        )
        ''')
        print("Table comment_votes created or already exists")

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_bans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            banned_by INTEGER NOT NULL,
            reason TEXT,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            UNIQUE(user_id),
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (banned_by) REFERENCES users (id)
        )
        ''')
        print("Table user_bans created or already exists")

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS moderation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            moderator_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            target_type TEXT NOT NULL,
            target_id INTEGER,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (moderator_id) REFERENCES users (id)
        )
        ''')
        print("Table moderation_logs created or already exists")

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id INTEGER NOT NULL,
            content_type TEXT NOT NULL,
            content_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_by INTEGER,
            reviewed_at TIMESTAMP,
            FOREIGN KEY (reporter_id) REFERENCES users (id),
            FOREIGN KEY (reviewed_by) REFERENCES users (id)
        )
        ''')
        print("Table reports created or already exists")

        print("Creating indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_at DESC)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_community ON posts(community_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_posts_user ON posts(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_comments_parent ON comments(parent_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_comment_votes_comment ON comment_votes(comment_id)')
        print("Indexes created successfully")

        cursor.execute("SELECT id FROM users WHERE role = 'admin'")
        if not cursor.fetchone():
            print("No admin found, creating default admin...")
            admin_hash = generate_password_hash('admin123')
            cursor.execute(
                "INSERT INTO users (username, display_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
                ('admin', 'Administrator', 'admin@example.com', admin_hash, 'admin')
            )
            print("Default admin created: admin / admin123")

        cursor.execute("SELECT id FROM users WHERE role = 'moderator'")
        if not cursor.fetchone():
            print("No moderator found, creating default moderator...")
            mod_hash = generate_password_hash('mod123')
            cursor.execute(
                "INSERT INTO users (username, display_name, email, password_hash, role) VALUES (?, ?, ?, ?, ?)",
                ('moderator', 'Moderator', 'mod@example.com', mod_hash, 'moderator')
            )
            print("Default moderator created: moderator / mod123")

        conn.commit()
        print("\n=== DATABASE UPDATE COMPLETE ===")
    except Exception as e:
        print(f"Error updating database: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


def reset_database():
    print("=== RESETTING DATABASE ===")
    if os.path.exists('instance/app.db'):
        os.remove('instance/app.db')
        print("Old database removed")
    init_database()


def show_database_status():
    if not os.path.exists('instance/app.db'):
        print("Database does not exist!")
        return
    conn = sqlite3.connect('instance/app.db')
    cursor = conn.cursor()
    print("=== DATABASE STATUS ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables ({len(tables)}):")
    for table in tables:
        print(f"  - {table[0]}")
    print("\n=== USERS ===")
    cursor.execute("SELECT id, username, display_name, role, is_banned, created_at FROM users")
    users = cursor.fetchall()
    for user in users:
        banned = " [BANNED]" if user[4] else ""
        print(f"  ID: {user[0]}, Username: {user[1]}, Display: {user[2]}, Role: {user[3]}{banned}, Created: {user[5]}")
    print("\n=== COMMUNITIES ===")
    cursor.execute('''
        SELECT c.id, c.name, c.display_name, u.username, c.subscribers_count
        FROM communities c
        JOIN users u ON c.owner_id = u.id
    ''')
    communities = cursor.fetchall()
    for c in communities:
        print(f"  ID: {c[0]}, Name: {c[1]}, Owner: {c[3]}, Subscribers: {c[4]}")
    print("\n=== POSTS ===")
    cursor.execute('''
        SELECT p.id, p.title[:40] as title, u.username, c.name as community, p.upvotes - p.downvotes as score
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN communities c ON p.community_id = c.id
        ORDER BY p.created_at DESC
        LIMIT 15
    ''')
    posts = cursor.fetchall()
    for p in posts:
        comm = f" [r/{p[3]}]" if p[3] else " [global]"
        print(f"  ID: {p[0]}, {p[1]}... by {p[2]}{comm} score: {p[4]}")
    print("\n=== COMMENTS (with nesting) ===")
    cursor.execute('''
        SELECT c.id, c.content[:50] as content, u.username, 
               c.parent_id, c.post_id
        FROM comments c
        JOIN users u ON c.user_id = u.id
        ORDER BY c.created_at DESC
        LIMIT 15
    ''')
    comments = cursor.fetchall()
    for c in comments:
        parent = f" (reply to {c[3]})" if c[3] else ""
        print(f"  ID: {c[0]}, Author: {c[2]}, Content: {c[1]}{parent}")
    conn.close()


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == 'reset':
            reset_database()
        elif sys.argv[1] == 'update':
            update_database()
        elif sys.argv[1] == 'status':
            show_database_status()
        else:
            print(f"Unknown command: {sys.argv[1]}")
            print("Available commands:")
            print("  python init_db.py          - Initialize new database")
            print("  python init_db.py reset    - Reset database completely")
            print("  python init_db.py update   - Update existing database")
            print("  python init_db.py status   - Show database status")
    else:
        init_database()
