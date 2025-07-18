from pysqlite2 import dbapi2 as sqlite
import re
import math

def getwords(doc):
    splitter = re.compile(r'\W*')
    print(doc)
    # Split the words by non-alpha characters
    words = [s.lower() for s in splitter.split(doc)
             if len(s) > 2 and len(s) < 20]
    # Return the unique set of words only
    return dict([(w, 1) for w in words])

class classifier:
    def __init__(self, getfeatures, filename=None):
        self.fc = {}
        self.cc = {}
        self.getfeatures = getfeatures

    def setdb(self, dbfile):
        self.con = sqlite.connect(dbfile)
        self.con.execute('create table if not exists fc(feature,category,count)')
        self.con.execute('create table if not exists cc(category,count)')

    def incf(self, f, cat):
        count = self.fcount(f, cat)
        if count == 0:
            self.con.execute("insert into fc values (?, ?, 1)", (f, cat))
        else:
            self.con.execute("update fc set count=? where feature=? and category=?",
                             (count + 1, f, cat))

    def fcount(self, f, cat):
        res = self.con.execute(
            'select count from fc where feature=? and category=?',
            (f, cat)).fetchone()
        if res is None:
            return 0
        else:
            return float(res[0])

    def incc(self, cat):
        count = self.catcount(cat)
        if count == 0:
            self.con.execute("insert into cc values (?,1)", (cat,))
        else:
            self.con.execute("update cc set count=? where category=?",
                             (count + 1, cat))

    def catcount(self, cat):
        res = self.con.execute(
            'select count from cc where category=?', (cat,)).fetchone()
        if res is None:
            return 0
        else:
            return float(res[0])

    def categories(self):
        cur = self.con.execute('select category from cc')
        return [d[0] for d in cur]

    def totalcount(self):
        res = self.con.execute('select sum(count) from cc').fetchone()
        if res is None:
            return 0
        return res[0]

    def train(self, item, cat):
        features = self.getfeatures(item)
        for f in features:
            self.incf(f, cat)
        self.incc(cat)
        self.con.commit()

    def fprob(self, f, cat):
        if self.catcount(cat) == 0:
            return 0
        return self.fcount(f, cat) / self.catcount(cat)

    def weightedprob(self, f, cat, prf, weight=1.0, ap=0.5):
        basicprob = prf(f, cat)
        totals = sum([self.fcount(f, c) for c in self.categories()])
        bp = ((weight * ap) + (totals * basicprob)) / (weight + totals)
        return bp

class naivebayes(classifier):
    def __init__(self, getfeatures):
        super().__init__(getfeatures)
        self.thresholds = {}

    def docprob(self, item, cat):
        features = self.getfeatures(item)
        p = 1
        for f in features:
            p *= self.weightedprob(f, cat, self.fprob)
        return p

    def prob(self, item, cat):
        catprob = self.catcount(cat) / self.totalcount()
        docprob = self.docprob(item, cat)
        return docprob * catprob

    def setthreshold(self, cat, t):
        self.thresholds[cat] = t

    def getthreshold(self, cat):
        return self.thresholds.get(cat, 1.0)

    def classify(self, item, default=None):
        probs = {}
        max_prob = 0.0
        best = None
        for cat in self.categories():
            probs[cat] = self.prob(item, cat)
            if probs[cat] > max_prob:
                max_prob = probs[cat]
                best = cat
        for cat in probs:
            if cat == best:
                continue
            if probs[cat] * self.getthreshold(best) > probs[best]:
                return default
        return best

class fisherclassifier(classifier):
    def __init__(self, getfeatures):
        super().__init__(getfeatures)
        self.minimums = {}

    def cprob(self, f, cat):
        clf = self.fprob(f, cat)
        if clf == 0:
            return 0
        freqsum = sum([self.fprob(f, c) for c in self.categories()])
        return clf / freqsum

    def fisherprob(self, item, cat):
        p = 1
        features = self.getfeatures(item)
        for f in features:
            p *= self.weightedprob(f, cat, self.cprob)
        fscore = -2 * math.log(p)
        return self.invchi2(fscore, len(features) * 2)

    def invchi2(self, chi, df):
        m = chi / 2.0
        sum = term = math.exp(-m)
        for i in range(1, df // 2):
            term *= m / i
            sum += term
        return min(sum, 1.0)

    def setminimum(self, cat, minval):
        self.minimums[cat] = minval

    def getminimum(self, cat):
        return self.minimums.get(cat, 0)

    def classify(self, item, default=None):
        best = default
        max_prob = 0.0
        for c in self.categories():
            p = self.fisherprob(item, c)
            if p > self.getminimum(c) and p > max_prob:
                best = c
                max_prob = p
        return best

def sampletrain(cl):
    cl.train('Nobody owns the water.', 'good')
    cl.train('the quick rabbit jumps fences', 'good')
    cl.train('buy pharmaceuticals now', 'bad')
    cl.train('make quick money at the online casino', 'bad')
    cl.train('the quick brown fox jumps', 'good')