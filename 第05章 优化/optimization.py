import time
import random
import math

people = [('Seymour', 'BOS'),
          ('Franny', 'DAL'),
          ('Zooey', 'CAK'),
          ('Walt', 'MIA'),
          ('Buddy', 'ORD'),
          ('Les', 'OMA')]

destination = 'LGA'
flights = {}

# 打开文件：用 open 替代 Python2 的 file 函数
with open('schedule.txt') as f:  # Python 3 中没有 file() 函数了
    for line in f:
        origin, dest, depart, arrive, price = line.strip().split(',')
        flights.setdefault((origin, dest), [])
        flights[(origin, dest)].append((depart, arrive, int(price)))

def getminutes(t):
    x = time.strptime(t, '%H:%M')
    return x.tm_hour * 60 + x.tm_min  # Python 3 中结构体字段需用 .tm_hour

def printschedule(r):
    for d in range(len(r) // 2):  # Python 3 中除法返回 float，需用 //
        name = people[d][0]
        origin = people[d][1]
        out = flights[(origin, destination)][int(r[d])]
        ret = flights[(destination, origin)][int(r[d + 1])]
        print('%10s%10s %5s-%5s $%3s %5s-%5s $%3s' % (
            name, origin, out[0], out[1], out[2], ret[0], ret[1], ret[2]
        ))  # Python 3 中 print 必须是函数形式

def schedulecost(sol):
    totalprice = 0
    latestarrival = 0
    earliestdep = 24 * 60

    for d in range(len(sol) // 2):  # Python 3 中 / 替换为 //
        origin = people[d][1]
        outbound = flights[(origin, destination)][int(sol[d])]
        returnf = flights[(destination, origin)][int(sol[d + 1])]

        totalprice += outbound[2]
        totalprice += returnf[2]

        if latestarrival < getminutes(outbound[1]):
            latestarrival = getminutes(outbound[1])
        if earliestdep > getminutes(returnf[0]):
            earliestdep = getminutes(returnf[0])

    totalwait = 0
    for d in range(len(sol) // 2):
        origin = people[d][1]
        outbound = flights[(origin, destination)][int(sol[d])]
        returnf = flights[(destination, origin)][int(sol[d + 1])]
        totalwait += latestarrival - getminutes(outbound[1])
        totalwait += getminutes(returnf[0]) - earliestdep

    if latestarrival > earliestdep:
        totalprice += 50

    return totalprice + totalwait

def randomoptimize(domain, costf):
    best = float('inf')  # Python 3 推荐用 float('inf') 表示无穷大
    bestr = None
    for i in range(1000):
        r = [float(random.randint(domain[i][0], domain[i][1]))
             for i in range(len(domain))]
        cost = costf(r)
        if cost < best:
            best = cost
            bestr = r
    return bestr  # 原代码这里误写为 return r，应返回 bestr

def hillclimb(domain, costf):
    sol = [random.randint(domain[i][0], domain[i][1])
           for i in range(len(domain))]

    while True:  # Python 3 中推荐写 while True
        neighbors = []

        for j in range(len(domain)):
            if sol[j] > domain[j][0]:
                neighbors.append(sol[0:j] + [sol[j] - 1] + sol[j + 1:])
            if sol[j] < domain[j][1]:
                neighbors.append(sol[0:j] + [sol[j] + 1] + sol[j + 1:])

        current = costf(sol)
        best = current
        for j in range(len(neighbors)):
            cost = costf(neighbors[j])
            if cost < best:
                best = cost
                sol = neighbors[j]

        if best == current:
            break
    return sol

def annealingoptimize(domain, costf, T=10000.0, cool=0.95, step=1):
    vec = [float(random.randint(domain[i][0], domain[i][1]))
           for i in range(len(domain))]

    while T > 0.1:
        i = random.randint(0, len(domain) - 1)
        dir = random.randint(-step, step)

        vecb = vec[:]
        vecb[i] += dir
        if vecb[i] < domain[i][0]:
            vecb[i] = domain[i][0]
        elif vecb[i] > domain[i][1]:
            vecb[i] = domain[i][1]

        ea = costf(vec)
        eb = costf(vecb)
        p = pow(math.e, (-eb - ea) / T)

        if eb < ea or random.random() < p:
            vec = vecb

        T = T * cool
    return vec

def geneticoptimize(domain, costf, popsize=50, step=1,
                    mutprob=0.2, elite=0.2, maxiter=100):

    def mutate(vec):
        i = random.randint(0, len(domain) - 1)
        if random.random() < 0.5 and vec[i] > domain[i][0]:
            return vec[0:i] + [vec[i] - step] + vec[i + 1:]
        elif vec[i] < domain[i][1]:
            return vec[0:i] + [vec[i] + step] + vec[i + 1:]
        return vec  # 增加 fallback 防止 None 返回

    def crossover(r1, r2):
        i = random.randint(1, len(domain) - 2)
        return r1[0:i] + r2[i:]

    pop = []
    for i in range(popsize):
        vec = [random.randint(domain[i][0], domain[i][1])
               for i in range(len(domain))]
        pop.append(vec)

    topelite = int(elite * popsize)

    for i in range(maxiter):
        scores = [(costf(v), v) for v in pop]
        scores.sort()
        ranked = [v for (s, v) in scores]

        pop = ranked[0:topelite]

        while len(pop) < popsize:
            if random.random() < mutprob:
                c = random.randint(0, topelite - 1)
                pop.append(mutate(ranked[c]))
            else:
                c1 = random.randint(0, topelite - 1)
                c2 = random.randint(0, topelite - 1)
                pop.append(crossover(ranked[c1], ranked[c2]))

        print(scores[0][0])  # Python 3 中 print 需加括号

    return scores[0][1]
