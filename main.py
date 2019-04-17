import options
import vk


data = []

try:
    # Initializing api object
    session = None

    if options.auth_type == 'token':
        session = vk.Session(access_token=options.access_token)
    elif options.auth_type == 'userpass':
        session = vk.AuthSession('id_app', options.login, options.password, scope='wall')

    api = vk.API(session)

    # posts = api.wall.get(
    #     v='5.95',
    #     # owner_id='39199554',
    #     domain='perawki',
    #     count='3'
    # )
    #
    # print(posts)

    # comments = api.wall.getComments(
    #     v='5.95',
    #     owner_id='39199554',
    #     post_id='103',
    #     need_likes=1,
    #     count='100',
    #     sort='asc'
    # )

    # Getting number of comments of a post
    comments_number = api.wall.getComments(
        v=options.api_version,
        owner_id=options.owner_id,
        post_id=options.post_id,
        count=1
    )

    # Getting all comments of a post
    for i in range(0, comments_number['count'], 100):
        comments = api.wall.getComments(
            v=options.api_version,
            owner_id=options.owner_id,
            post_id=options.post_id,
            need_likes=options.need_likes,
            count=options.count,
            sort=options.sort,
            thread_items_count=options.thread_items_count,
            offset=i
        )

        for j in range(0, len(comments['items'])):

            line = []

            for k in options.return_fields:
                line.append(comments['items'][j][k])

            data.append(line)
except Exception as e:
    print('Во время работы программы произошла ошибка:\n\t' + str(e))
finally:
    with open('out.csv', 'w') as f:
        for i in range(0, len(data)):
            for j in range (0, len(data[i])):
                if j != 0:
                    print(',', end='', file=f)
                print(data[i][j], end='', file=f)
            print(';', file=f)
