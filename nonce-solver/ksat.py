import numpy as np, time, sys, json
INIT=0.01

def bp(n, C, w, damping=0.5, iters=400, seed=0, tol=1e-5):
    """C: (m,k) signed ints. w: weight array len k+1 indexed by #true literals."""
    rng = np.random.default_rng(seed)
    m, k = C.shape
    var = np.abs(C) - 1; sgn = C > 0
    u = rng.normal(0, INIT, size=(m, k))
    for it in range(iters):
        H = np.zeros(n); np.add.at(H, var, u)
        cav = H[var] - u
        p1 = 1/(1+np.exp(-np.clip(cav, -40, 40)))
        pt = np.where(sgn, p1, 1-p1)
        new = np.empty_like(u)
        for a in range(k):
            others = [j for j in range(k) if j != a]
            # distribution of #true among others (poly multiply)
            d = np.zeros((m, k)); d[:, 0] = 1
            for j in others:
                p = pt[:, j:j+1]
                d = d*(1-p) + np.concatenate([np.zeros((m,1)), d[:, :-1]], 1)*p
            ft = (d*w[1:]).sum(1); ff = (d*w[:-1]).sum(1)
            r = np.log(ft+1e-300) - np.log(ff+1e-300)
            new[:, a] = np.where(sgn[:, a], r, -r)
        delta = np.max(np.abs(new-u))
        u = damping*u + (1-damping)*new
        if delta < tol: break
    H = np.zeros(n); np.add.at(H, var, u)
    return (H > 0).astype(np.int8), H

def nunsat(x, C):
    v = np.abs(C)-1; s = C > 0
    return int((~np.where(s, x[v] == 1, x[v] == 0).any(1)).sum())

def walksat(x, n, C, maxflips=3_000_000, p=0.25, seed=0, tlimit=120):
    rng = np.random.default_rng(seed); t0 = time.time()
    m, k = C.shape
    var = (np.abs(C)-1).tolist(); pos = (C > 0).tolist()
    occ = [[] for _ in range(n)]
    for i in range(m):
        for j in range(k): occ[var[i][j]].append((i, j))
    x = [int(v) for v in x]
    nt = [sum((x[var[i][j]] == 1) == pos[i][j] for j in range(k)) for i in range(m)]
    U = [i for i in range(m) if nt[i] == 0]; where = {c: idx for idx, c in enumerate(U)}
    def add(c):
        where[c] = len(U); U.append(c)
    def rem(c):
        idx = where.pop(c); last = U.pop()
        if last != c: U[idx] = last; where[last] = idx
    rnd = rng.random(maxflips); ri = rng.integers(0, 1 << 30, maxflips)
    for f in range(maxflips):
        if not U: return np.array(x, dtype=np.int8), 0
        if f % 20000 == 0 and time.time()-t0 > tlimit: break
        c = U[ri[f] % len(U)]
        vs = var[c]
        best, bv = None, None
        for v in vs:
            b = 0
            for (i, j) in occ[v]:
                if nt[i] == 1 and (x[v] == 1) == pos[i][j]: b += 1
            if best is None or b < best: best, bv = b, v
        if best > 0 and rnd[f] < p: bv = vs[ri[f] % k]
        v = bv
        for (i, j) in occ[v]:
            if (x[v] == 1) == pos[i][j]:
                nt[i] -= 1
                if nt[i] == 0: add(i)
            else:
                if nt[i] == 0: rem(i)
                nt[i] += 1
        x[v] ^= 1
    return np.array(x, dtype=np.int8), len(U)

def solve(n, clauses, tlimit=600):
    C = np.array(clauses, dtype=np.int64); k = C.shape[1]; t0 = time.time()
    best = None
    for q in (None, 0.618, 0.5, 0.8):
        w = np.ones(k+1); w[0] = 0
        if q is not None: w = np.array([0]+[q**j for j in range(1, k+1)])
        for seed, d in [(0, .5), (1, .7)]:
            x, H = bp(n, C, w, damping=d, seed=seed)
            u = nunsat(x, C)
            print(f'q={q} d={d} unsat={u} t={time.time()-t0:.1f}', file=sys.stderr)
            if u == 0: return ''.join(map(str, x))
            if best is None or u < best[0]: best = (u, x)
    x = best[1]; s = 0
    while time.time()-t0 < tlimit:
        x2, u = walksat(x, n, C, seed=s, tlimit=min(120, tlimit-(time.time()-t0)))
        print(f'walksat seed={s} unsat={u} t={time.time()-t0:.1f}', file=sys.stderr)
        if u == 0: return ''.join(map(str, x2))
        s += 1
    return None

def gen_balanced(n, m, k=5, seed=0):
    # planted, balanced: keep clauses with prob ~ q^j to hide planted signal
    rng = np.random.default_rng(seed); h = rng.integers(0, 2, n); out = []
    q = 0.618
    while len(out) < m:
        v = rng.choice(n, k, replace=False); s = rng.integers(0, 2, k)
        j = int(((h[v] == 1) == (s == 1)).sum())
        if j and rng.random() < q**j: out.append([int(a+1) if b else -int(a+1) for a, b in zip(v, s)])
    return out

if __name__ == '__main__':
    n, m = 1536, 33792
    cl = gen_balanced(n, m); t = time.time(); r = solve(n, cl, tlimit=100)
    print('solved' if r else 'FAILED', f'{time.time()-t:.1f}s')
