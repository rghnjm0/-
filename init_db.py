import sqlite3
import hashlib
from werkzeug.security import generate_password_hash
import os
import sys
import random
from datetime import datetime, timedelta


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
        print("Creating admin, moderator and test users...")
        
        # Создаем администратора
        admin_hash = generate_password_hash('admin123')
        cursor.execute(
            "INSERT INTO users (username, display_name, email, password_hash, role, karma, bio, avatar_color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ('admin', 'Administrator', 'admin@example.com', admin_hash, 'admin', 500, 'Главный администратор платформы', '#e8402a')
        )
        admin_id = cursor.lastrowid
        print(f"Admin created with ID: {admin_id} (login: admin, password: admin123)")

        # Создаем модератора
        mod_hash = generate_password_hash('mod123')
        cursor.execute(
            "INSERT INTO users (username, display_name, email, password_hash, role, karma, bio, avatar_color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ('moderator', 'Moderator', 'mod@example.com', mod_hash, 'moderator', 350, 'Модератор сообществ', '#2563eb')
        )
        mod_id = cursor.lastrowid
        print(f"Moderator created with ID: {mod_id} (login: moderator, password: mod123)")

        # Создаем тестовых пользователей
        test_users = [
            ('alex_tech', 'Alex Tech', 'alex@example.com', 120, 'Программист и энтузиаст технологий', '#16a34a'),
            ('maria_art', 'Maria Art', 'maria@example.com', 85, 'Художник-иллюстратор', '#d97706'),
            ('pavel_games', 'Pavel Games', 'pavel@example.com', 200, 'Геймер и стример', '#9333ea'),
            ('olga_photo', 'Olga Photo', 'olga@example.com', 45, 'Фотограф-любитель', '#0891b2'),
            ('denis_music', 'Denis Music', 'denis@example.com', 67, 'Музыкант и мелломан', '#db2777'),
            ('anna_life', 'Anna Life', 'anna@example.com', 92, 'Блогер о жизни', '#64748b'),
            ('sergey_dev', 'Sergey Dev', 'sergey@example.com', 156, 'Full-stack разработчик', '#e8402a'),
            ('kate_food', 'Kate Food', 'kate@example.com', 78, 'Кулинарный блогер', '#2563eb')
        ]
        
        test_user_ids = []
        for username, display_name, email, karma, bio, avatar_color in test_users:
            pw_hash = generate_password_hash('test123')
            cursor.execute(
                "INSERT INTO users (username, display_name, email, password_hash, role, karma, bio, avatar_color) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (username, display_name, email, pw_hash, 'user', karma, bio, avatar_color)
            )
            test_user_ids.append(cursor.lastrowid)
        
        all_users = [admin_id, mod_id] + test_user_ids
        print(f"Created {len(all_users)} users total")

        # Создаем сообщества
        print("Creating communities...")
        
        communities_data = [
            ('techworld', 'Tech World', 'Обсуждаем технологии, программирование, гаджеты и IT-новости', admin_id, True),
            ('artgallery', 'Art Gallery', 'Место для художников и любителей искусства. Делитесь своими работами!', mod_id, True),
            ('gamershub', 'Gamers Hub', 'Все о видеоиграх: новинки, обзоры, советы и обсуждения', mod_id, True),
            ('photography', 'Photography', 'Сообщество фотографов: от новичков до профессионалов', admin_id, True)
        ]
        
        community_ids = []
        for name, display_name, description, owner_id, is_public in communities_data:
            cursor.execute(
                "INSERT INTO communities (name, display_name, description, owner_id, is_public) VALUES (?, ?, ?, ?, ?)",
                (name, display_name, description, owner_id, is_public)
            )
            community_ids.append(cursor.lastrowid)
        
        # Подписываем пользователей на сообщества
        print("Creating subscriptions...")
        for user_id in all_users:
            # Каждый пользователь подписан на 2-3 случайных сообщества
            subs = random.sample(community_ids, random.randint(2, 3))
            for comm_id in subs:
                cursor.execute(
                    "INSERT OR IGNORE INTO community_subscriptions (user_id, community_id) VALUES (?, ?)",
                    (user_id, comm_id)
                )
        
        # Обновляем счетчики подписчиков
        for comm_id in community_ids:
            cursor.execute(
                "UPDATE communities SET subscribers_count = (SELECT COUNT(*) FROM community_subscriptions WHERE community_id = ?) WHERE id = ?",
                (comm_id, comm_id)
            )
        
        # Создаем посты
        print("Creating posts...")
        
        posts_data = [
            # Tech World посты
            ('Новый фреймворк для веб-разработки: что вы думаете?',
             '<p>Недавно вышел новый фреймворк <strong>Astro 5.0</strong>. Кто уже пробовал? Какие впечатления?</p><p>По сравнению с Next.js и Nuxt, что лучше для нового проекта?</p>',
             admin_id, community_ids[0], 15, 2, 8),
            ('Как начать изучать Python с нуля в 2026 году',
             '<p>Собрал подборку лучших ресурсов для начинающих:</p><ul><li><strong>Книги:</strong> "Автоматизация рутинных задач с Python"</li><li><strong>Курсы:</strong> Stepik, Coursera</li><li><strong>YouTube:</strong> Тимофей Хирьянов</li></ul><p>Делитесь своими советами!</p>',
             test_user_ids[0], community_ids[0], 28, 3, 15),
            ('Сравнение языков программирования: Rust vs Go',
             '<p>Какой язык выбрать для высоконагруженных систем? Rust предлагает безопасность памяти, Go — простоту и горутины.</p><p>Ваше мнение? Какие проекты на этих языках вы делали?</p>',
             test_user_ids[6], community_ids[0], 42, 5, 24),
            
            # Art Gallery посты
            ('Моя новая цифровая иллюстрация "Лесной дух"',
             '<p>Работал над этой иллюстрацией около двух недель. Использовал Procreate и Photoshop для финальной обработки.</p><p><img src="https://placehold.co/600x400/e8402a/white?text=Forest+Spirit" alt="Иллюстрация" style="max-width:100%;border-radius:8px"></p><p>Буду рад конструктивной критике!</p>',
             test_user_ids[1], community_ids[1], 52, 2, 31),
            ('Советы по анатомии для начинающих художников',
             '<p>Собрал полезные ресурсы по анатомии:</p><ul><li>Книга "Анатомия для художников" Дж. Харт</li><li>YouTube-канал Proko</li><li>Приложение "Anatomy 3D"</li></ul><p>Как вы изучали анатомию?</p>',
             test_user_ids[1], community_ids[1], 18, 1, 9),
            
            # Gamers Hub посты
            ('Обзор новинки: Elden Ring 2 — первые впечатления',
             '<p>Сыграл первые 10 часов в Elden Ring 2. Графика стала лучше, боевая система доработана, но сложность все так же высока.</p><p><strong>Плюсы:</strong></p><ul><li>Открытый мир стал более живым</li><li>Новые классы и билды</li><li>Кооператив работает отлично</li></ul><p><strong>Минусы:</strong></p><ul><li>Оптимизация на ПК хромает</li><li>Не хватает маркеров для квестов</li></ul><p>А вы уже играли? Делитесь мнением!</p>',
             test_user_ids[2], community_ids[2], 89, 12, 47),
            ('Лучшие инди-игры 2025 года: моя подборка',
             '<p>В этом году вышло много отличных инди-проектов. Вот мой топ-5:</p><ol><li><strong>Hollow Knight: Silksong</strong> — наконец-то вышла!</li><li><strong>Stray 2</strong> — новый кот-приключение</li><li><strong>Hades 2</strong> — полная версия</li><li><strong>Animal Well</strong> — атмосферный метроидвания</li><li><strong>Pacific Drive</strong> — уникальный автомобильный рогалик</li></ol><p>Что добавите?</p>',
             test_user_ids[2], community_ids[2], 67, 4, 38),
            ('Как улучшить FPS в играх: практические советы',
             '<p>Настройки, которые реально помогают:</p><ul><li>Выключить вертикальную синхронизацию</li><li>Снизить качество теней</li><li>Отключить сглаживание</li><li>Обновить драйвера видеокарты</li></ul><p>У кого какие лайфхаки?</p>',
             test_user_ids[0], community_ids[2], 34, 6, 19),
            
            # Photography посты
            ('Уличная фотография: как поймать момент',
             '<p>Делюсь опытом съемки на улице:</p><ul><li>Используйте быстрый объектив (f/1.8-2.8)</li><li>Снимайте в RAW</li><li>Ищите интересные светотени</li><li>Будьте незаметны для естественных кадров</li></ul><p>Вот пример из моей последней серии:</p><p><img src="https://placehold.co/600x400/2563eb/white?text=Street+Photo" alt="Уличное фото" style="max-width:100%;border-radius:8px"></p>',
             test_user_ids[3], community_ids[3], 41, 3, 22),
            ('Выбор камеры для начинающего фотографа',
             '<p>Какую камеру выбрать в 2026?</p><p><strong>Бюджет до 500$:</strong></p><ul><li>Sony A6000 — отличный выбор для старта</li><li>Canon EOS 2000D — простота использования</li></ul><p><strong>Бюджет 500-1000$:</strong></p><ul><li>Fujifilm X-T30 — лучшая цветопередача</li><li>Sony A6400 — автофокус и видео</li></ul><p>На чем снимаете вы?</p>',
             test_user_ids[3], community_ids[3], 23, 2, 14)
        ]
        
        post_ids = []
        for title, content, user_id, community_id, upvotes, downvotes, comments_count in posts_data:
            # Создаем пост с разными датами (от 1 до 30 дней назад)
            days_ago = random.randint(1, 30)
            created_at = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
            created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
            
            cursor.execute(
                "INSERT INTO posts (title, content, user_id, community_id, upvotes, downvotes, comments_count, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (title, content, user_id, community_id, upvotes, downvotes, comments_count, created_at_str)
            )
            post_ids.append(cursor.lastrowid)
        
        # Добавляем голоса за посты
        print("Creating votes...")
        for post_id in post_ids:
            # Случайные пользователи голосуют за посты
            voters = random.sample(all_users, random.randint(5, 15))
            for voter in voters:
                vote_type = random.choice(['up', 'down'])
                cursor.execute(
                    "INSERT OR IGNORE INTO votes (user_id, post_id, vote_type) VALUES (?, ?, ?)",
                    (voter, post_id, vote_type)
                )
        
        # Создаем комментарии
        print("Creating comments...")
        
        comments_data = [
            # Пост 1 (Tech World - новый фреймворк)
            (post_ids[0], test_user_ids[0], 'Пробовал Astro 4.0, впечатления отличные. Особенно понравилась интеграция с React и Vue одновременно. Обязательно попробую 5.0!', None),
            (post_ids[0], test_user_ids[6], 'Я за Next.js, он более зрелый и с большим комьюнити. Astro пока не хватает экосистемы.', None),
            (post_ids[0], test_user_ids[2], 'А если проект на Svelte? У Astro отличная поддержка!', None),
            (post_ids[0], test_user_ids[6], 'Согласен, для Svelte это отличный выбор!', None),
            
            # Пост 2 (Python для начинающих)
            (post_ids[1], test_user_ids[2], 'Отличная подборка! Еще посоветую канал "Типичный программист" - очень понятно объясняет.', None),
            (post_ids[1], mod_id, 'Согласен, Python - лучший язык для старта. Добавлю еще ресурс "Pythonist.ru" с задачами.', None),
            (post_ids[1], test_user_ids[0], 'Начинал с книги "Укус питона" - тоже отличный вариант!', None),
            
            # Пост 3 (Rust vs Go)
            (post_ids[2], admin_id, 'Rust для системного программирования, Go для микросервисов. Каждый хорош в своей нише!', None),
            (post_ids[2], test_user_ids[6], 'Пишу на Go уже 3 года, для бэкенда - идеально. Rust сложноват для быстрой разработки.', None),
            (post_ids[2], test_user_ids[0], 'А почему не рассматриваете Zig? Тоже интересный язык набирает популярность.', None),
            
            # Пост 4 (Иллюстрация)
            (post_ids[3], test_user_ids[1], 'Потрясающая работа! Очень атмосферно. Как долго работали над деталями?', None),
            (post_ids[3], test_user_ids[1], 'Спасибо! На детали ушло около 3 дней, все остальное - композиция и цвета.', None),
            (post_ids[3], test_user_ids[2], 'Цветовая гамма просто шикарная! Использовали готовые палитры или сами подбирали?', None),
            
            # Пост 5 (Анатомия)
            (post_ids[4], test_user_ids[1], 'Proko - это база! Еще очень помог курс "Анатомия для художников" на Skillshare.', None),
            (post_ids[4], test_user_ids[2], 'А есть хорошие приложения для iPad?', None),
            (post_ids[4], test_user_ids[1], 'Да, "Complete Anatomy" и "Anatomy 3D Atlas" - отличные варианты!', None),
            
            # Пост 6 (Elden Ring 2)
            (post_ids[5], test_user_ids[0], 'Играл на PS5, оптимизация отличная. На ПК правда есть проблемы с RTX.', None),
            (post_ids[5], test_user_ids[2], 'Согласен, на ПК подтормаживает. Но игра стоит того, графика невероятная!', None),
            (post_ids[5], mod_id, 'Как вам новые боссы? Я пока только до первого добрался, но уже в восторге!', None),
            (post_ids[5], test_user_ids[2], 'Боссы сложные, но справедливые. Как и в первой части - учим паттерны и побеждаем!', None),
            
            # Пост 7 (Инди-игры)
            (post_ids[6], admin_id, 'Animal Well - шедевр! Прошел на 100%, атмосфера невероятная.', None),
            (post_ids[6], test_user_ids[1], 'А я залип в Hades 2, уже 50+ часов, и не надоедает!', None),
            (post_ids[6], test_user_ids[3], 'Pacific Drive - очень недооцененная игра, рекомендую всем!', None),
            
            # Пост 8 (FPS)
            (post_ids[7], test_user_ids[2], 'Еще совет: отключите тени и эффекты пост-обработки. Дает +15-20 FPS!', None),
            (post_ids[7], test_user_ids[6], 'DLSS/FSR тоже очень помогает на современных картах.', None),
            (post_ids[7], mod_id, 'А если игра старая, можно попробовать SpecialK или другие моды для оптимизации.', None),
            
            # Пост 9 (Уличная фотография)
            (post_ids[8], test_user_ids[1], 'Отличные советы! А какой объектив используете для улицы?', None),
            (post_ids[8], test_user_ids[3], 'Снимаю на 35mm f/1.8. Отличный универсальный фокус для уличной съемки.', None),
            (post_ids[8], test_user_ids[2], 'Как относитесь к съемке на телефон? В последнее время многие переходят.', None),
            (post_ids[8], test_user_ids[3], 'Телефоны стали хороши, но для настоящей уличной фотографии все же нужна камера - больше контроля!', None),
            
            # Пост 10 (Выбор камеры)
            (post_ids[9], test_user_ids[1], 'Начинал с Sony A6000, до сих пор считаю лучшим выбором для новичка!', None),
            (post_ids[9], test_user_ids[2], 'А что скажете про беззеркалки Canon?', None),
            (post_ids[9], test_user_ids[3], 'Canon EOS R10 - отличная камера для старта. Удобное меню и хорошая эргономика.', None),
            (post_ids[9], admin_id, 'Fujifilm X-T30 для меня - идеал. Цвета прямо с камеры без обработки.', None),
        ]
        
        comment_ids = []
        for comment in comments_data:
            post_id, user_id, content, parent_id = comment
            
            days_ago = random.randint(1, 25)
            created_at = datetime.now() - timedelta(days=days_ago, hours=random.randint(0, 23))
            created_at_str = created_at.strftime('%Y-%m-%d %H:%M:%S')
            
            # Случайные голоса
            upvotes = random.randint(0, 15)
            downvotes = random.randint(0, 5)
            
            cursor.execute(
                "INSERT INTO comments (content, user_id, post_id, parent_id, upvotes, downvotes, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (content, user_id, post_id, parent_id, upvotes, downvotes, created_at_str)
            )
            comment_ids.append(cursor.lastrowid)
        
        # Добавляем голоса за комментарии
        print("Creating comment votes...")
        for comment_id in comment_ids:
            voters = random.sample(all_users, random.randint(3, 10))
            for voter in voters:
                vote_type = random.choice(['up', 'down'])
                cursor.execute(
                    "INSERT OR IGNORE INTO comment_votes (user_id, comment_id, vote_type) VALUES (?, ?, ?)",
                    (voter, comment_id, vote_type)
                )
        
        # Обновляем счетчики комментариев в постах
        for post_id in post_ids:
            cursor.execute(
                "UPDATE posts SET comments_count = (SELECT COUNT(*) FROM comments WHERE post_id = ? AND is_deleted = 0) WHERE id = ?",
                (post_id, post_id)
            )
        
        conn.commit()
        print("Test data created successfully!")

    conn.commit()

    print("\n=== DATABASE CHECK ===")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"Tables created: {[t[0] for t in tables]}")
    
    cursor.execute("SELECT id, username, display_name, role, karma FROM users")
    users = cursor.fetchall()
    print(f"\nUsers in database ({len(users)}):")
    for user in users:
        print(f"  ID: {user[0]}, Username: {user[1]}, Display: {user[2]}, Role: {user[3]}, Karma: {user[4]}")
    
    cursor.execute("SELECT id, name, display_name, subscribers_count FROM communities")
    communities = cursor.fetchall()
    print(f"\nCommunities in database ({len(communities)}):")
    for comm in communities:
        print(f"  ID: {comm[0]}, Name: r/{comm[1]}, Display: {comm[2]}, Subscribers: {comm[3]}")
    
    cursor.execute("SELECT COUNT(*) FROM posts WHERE is_deleted = 0")
    posts_count = cursor.fetchone()[0]
    print(f"\nPosts in database: {posts_count}")
    
    cursor.execute("SELECT COUNT(*) FROM comments WHERE is_deleted = 0")
    comments_count = cursor.fetchone()[0]
    print(f"Comments in database: {comments_count}")
    
    cursor.execute("SELECT COUNT(*) FROM votes")
    votes_count = cursor.fetchone()[0]
    print(f"Votes in database: {votes_count}")
    
    cursor.execute("SELECT COUNT(*) FROM comment_votes")
    comment_votes_count = cursor.fetchone()[0]
    print(f"Comment votes in database: {comment_votes_count}")
    
    conn.close()
    print("\n=== DATABASE INITIALIZATION COMPLETE ===")
    print("Test credentials:")
    print("  Admin: admin / admin123")
    print("  Moderator: moderator / mod123")
    print("  Test users: alex_tech / test123, maria_art / test123, pavel_games / test123, etc.")


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
    cursor.execute("SELECT id, username, display_name, role, karma, is_banned, created_at FROM users")
    users = cursor.fetchall()
    for user in users:
        banned = " [BANNED]" if user[5] else ""
        print(f"  ID: {user[0]}, Username: {user[1]}, Display: {user[2]}, Role: {user[3]}, Karma: {user[4]}{banned}, Created: {user[6]}")
    print("\n=== COMMUNITIES ===")
    cursor.execute('''
        SELECT c.id, c.name, c.display_name, u.username, c.subscribers_count
        FROM communities c
        JOIN users u ON c.owner_id = u.id
    ''')
    communities = cursor.fetchall()
    for c in communities:
        print(f"  ID: {c[0]}, Name: r/{c[1]}, Owner: {c[3]}, Subscribers: {c[4]}")
    print("\n=== POSTS ===")
    cursor.execute('''
        SELECT p.id, p.title[:40], u.username, c.name, p.upvotes - p.downvotes as score
        FROM posts p
        JOIN users u ON p.user_id = u.id
        LEFT JOIN communities c ON p.community_id = c.id
        WHERE p.is_deleted = 0
        ORDER BY p.created_at DESC
        LIMIT 10
    ''')
    posts = cursor.fetchall()
    for p in posts:
        comm = f" in r/{p[3]}" if p[3] else ""
        print(f"  ID: {p[0]}, Title: {p[1]}{comm}, Author: {p[2]}, Score: {p[4]}")
    print("\n=== COMMENTS ===")
    cursor.execute('''
        SELECT c.id, c.content[:50] as content, u.username, 
               c.parent_id, c.post_id,
               c.upvotes - c.downvotes as score
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.is_deleted = 0
        ORDER BY c.created_at DESC
        LIMIT 15
    ''')
    comments = cursor.fetchall()
    for c in comments:
        parent = f" (reply to {c[3]})" if c[3] else ""
        print(f"  ID: {c[0]}, Author: {c[2]}, Score: {c[5]}, Content: {c[1]}{parent}")
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
