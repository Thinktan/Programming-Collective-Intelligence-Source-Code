import feedparser
import re

# Takes a filename or URL of a blog feed and classifies the entries
def read(feed, classifier):
    # Get feed entries and loop over them
    f = feedparser.parse(feed)
    for entry in f['entries']:
        print('-----')
        # Print the contents of the entry
        print('Title:     ' + entry['title'])
        print('Publisher: ' + entry.get('publisher', 'N/A'))
        print()
        print(entry['summary'])

        # Combine all the text to create one item for the classifier
        fulltext = '%s\n%s\n%s' % (
            entry['title'], entry.get('publisher', ''), entry['summary'])

        # Print the best guess at the current category
        print('Guess: ' + str(classifier.classify(entry)))

        # Ask the user to specify the correct category and train on that
        cl = input('Enter category: ')
        classifier.train(entry, cl)


def entryfeatures(entry):
    splitter = re.compile(r'\W*')
    f = {}

    # Extract the title words and annotate
    titlewords = [s.lower() for s in splitter.split(entry['title'])
                  if 2 < len(s) < 20]
    for w in titlewords:
        f['Title:' + w] = 1

    # Extract the summary words
    summarywords = [s.lower() for s in splitter.split(entry['summary'])
                    if 2 < len(s) < 20]

    # Count uppercase words
    uc = 0
    for i in range(len(summarywords)):
        w = summarywords[i]
        f[w] = 1
        if w.isupper():
            uc += 1

        # Get word pairs in summary as features
        if i < len(summarywords) - 1:
            twowords = ' '.join(summarywords[i:i + 2])
            f[twowords] = 1

    # Keep creator and publisher whole
    f['Publisher:' + entry.get('publisher', '')] = 1

    # UPPERCASE is a virtual word flagging too much shouting
    if len(summarywords) > 0 and float(uc) / len(summarywords) > 0.3:
        f['UPPERCASE'] = 1

    return f
