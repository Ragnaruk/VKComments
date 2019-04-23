from vkcomments import VKComments

# url = 'https://vk.com/vklive_app?w=wall-135678176_11436'
# url = 'https://vk.com/feed?w=wall-28122932_229001'
# url = 'https://vk.com/search?c%5Bper_page%5D=80&c%5Bq%5D=прямая&c%5Bsection%5D=video&c%5Bsort%5D=2&z=video-2784806_456239168'
# url = 'https://vk.com/feed?w=wall-28122932_228936'

comments = VKComments(url)
data = comments.get_comments()
comments.print_csv(data)
