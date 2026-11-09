from job_match_hunter.ingestion import html_to_string

# text = html_to_string(url='https://en.wikipedia.org/wiki/Computer_science')
# text = html_to_string(url='https://www.nn-careers.com/vacature/2955/ai-engineer-2?apply=1&utm_source=LinkedIn')
# text = html_to_string(url='https://ohpen.jobs.personio.com/job/2803224')
text = html_to_string(url='https://jobs.ashbyhq.com/bjakcareer/b1e73b18-5191-4c06-8f66-3ede3b88702b?utm_source=YmpnOkRB66')

print(text)
print(len(text))