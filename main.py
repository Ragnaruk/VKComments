from vkcomments import VKComments

url = 'https://vk.com/vklive_app?w=wall-135678176_11436'

comments = VKComments(url)
data = comments.get_comments()
comments.print_csv(data)
