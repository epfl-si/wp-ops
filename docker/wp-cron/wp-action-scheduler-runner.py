# TODO  run scheduler that will call OPDo API
from wordpresses import WordpressSite

if __name__ == '__main__':
    for wordpresssite in WordpressSite.all():
        print(wordpresssite.moniker)
        wordpresssite.run_action_scheduler_runner()

    exit(0)
