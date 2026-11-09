from job_match_hunter.ingestion import html_to_string

# text = html_to_string(url='https://en.wikipedia.org/wiki/Computer_science')
text = html_to_string(url='https://www.nn-careers.com/vacature/2955/ai-engineer-2?apply=1&utm_source=LinkedIn')

print(text)