import time

from wordpresses import WordpressSite

if __name__ == '__main__':
    for wordpresssite in WordpressSite.all():
        print(wordpresssite.moniker)
        print(wordpresssite.run_cron())

    print("All done. I am going to sleep", flush=True)
    time.sleep(3600)
