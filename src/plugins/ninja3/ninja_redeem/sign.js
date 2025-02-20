function parse(inputString) {
    const length = inputString.length;
    const outputArray = new Array((length + 3) >> 2).fill(0); // Ensure the output array can hold all values

    for (let index = 0; index < length; index++) {
        const charCode = inputString.charCodeAt(index);
        outputArray[index >> 2] |= (charCode & 0xFF) << (24 - (index % 4) * 8);
    }
    const sigBytes = length;
    return new WordArray(outputArray, sigBytes);
}

class WordArray {
    constructor(words = [], sigBytes = 0) {
        this.words = words; // Array of 32-bit words
        this.sigBytes = sigBytes; // Number of significant bytes
        this._map = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=";
    }

    concat(e) {
        var t = this.words
          , n = e.words
          , r = this.sigBytes
          , o = e.sigBytes;
        if (this.clamp(),
        r % 4)
            for (var i = 0; i < o; i++) {
                var a = n[i >>> 2] >>> 24 - i % 4 * 8 & 255;
                t[r + i >>> 2] |= a << 24 - (r + i) % 4 * 8
            }
        else
            for (var c = 0; c < o; c += 4)
                t[r + c >>> 2] = n[c >>> 2];
        return this.sigBytes += o,
        this
    }

    clamp() {
        var t = this.words
          , n = this.sigBytes;
        t[n >>> 2] &= 4294967295 << 32 - n % 4 * 8,
        t.length = Math.ceil(n / 4)
    }

    clone() {
        return new WordArray(this.words.slice(), this.sigBytes);
    }

    toString() {
        var t = this.words
        , n = this.sigBytes
        , r = this._map;
        this.clamp();
        for (var o = [], i = 0; i < n; i += 3)
            for (var a = (t[i >>> 2] >>> 24 - i % 4 * 8 & 255) << 16 | (t[i + 1 >>> 2] >>> 24 - (i + 1) % 4 * 8 & 255) << 8 | t[i + 2 >>> 2] >>> 24 - (i + 2) % 4 * 8 & 255, c = 0; c < 4 && i + .75 * c < n; c++)
                o.push(r.charAt(a >>> 6 * (3 - c) & 63));
        var u = r.charAt(64);
        if (u)
            for (; o.length % 4; )
                o.push(u);
        return o.join("")
    }
}



class Hasher {
    constructor() {
        this._data = new WordArray();
        this._hash = new WordArray(
            [892891647, 512507702, 1892448963, 1580381275, 1698316492],
            20
        );
        this._nDataBytes = 64;
        this._minBufferSize = 0;
        this.blockSize = 16;
    }

    _doReset() {
        this._hash = new WordArray([1732584193, 4023233417, 2562383102, 271733878, 3285377520], 20);
    }

    _doProcessBlock(e, t) {
        let u = [];
        for (var n = this._hash.words, r = n[0], o = n[1], i = n[2], a = n[3], c = n[4], s = 0; s < 80; s++) {
            if (s < 16)
                u[s] = 0 | e[t + s];
            else {
                var f = u[s - 3] ^ u[s - 8] ^ u[s - 14] ^ u[s - 16];
                u[s] = f << 1 | f >>> 31
            }
            var l = (r << 5 | r >>> 27) + c + u[s];
            l += s < 20 ? 1518500249 + (o & i | ~o & a) : s < 40 ? 1859775393 + (o ^ i ^ a) : s < 60 ? (o & i | o & a | i & a) - 1894007588 : (o ^ i ^ a) - 899497514,
            c = a,
            a = i,
            i = o << 30 | o >>> 2,
            o = r,
            r = l
        }
        n[0] = n[0] + r | 0,
        n[1] = n[1] + o | 0,
        n[2] = n[2] + i | 0,
        n[3] = n[3] + a | 0,
        n[4] = n[4] + c | 0
    }

    _doFinalize() {
        var e = this._data
          , t = e.words
          , n = 8 * this._nDataBytes
          , r = 8 * e.sigBytes;
        return t[r >>> 5] |= 128 << 24 - r % 32,
        t[14 + (r + 64 >>> 9 << 4)] = Math.floor(n / 4294967296),
        t[15 + (r + 64 >>> 9 << 4)] = n,
        e.sigBytes = 4 * t.length,
        this._process(),
        this._hash
    }

    _append(e) {
        "string" == typeof e && (e = parse(e)),
        this._data.concat(e),
        this._nDataBytes += e.sigBytes
    }

    _process() {
        let t = false;
        var n, r = this._data, o = r.words, i = r.sigBytes, a = this.blockSize, c = i / (4 * a), u = (c = t ? Math.ceil(c) : Math.max((0 | c) - this._minBufferSize, 0)) * a, s = Math.min(4 * u, i);
        if (u) {
            for (var l = 0; l < u; l += a)
                this._doProcessBlock(o, l);
            n = o.splice(0, u),
            r.sigBytes -= s
        }
        return new WordArray(n, s);
    }

    reset() {
        this._data = new WordArray([], 0);
        this._nDataBytes = 0;
        this._doReset()
    }

    update(e) {
        return this._append(e),
        this._process(),
        this
    }

    finalize(e) {
        return e && this._append(e),
        this._doFinalize()
    }
}

class HMAC {
    constructor() {
        this._hasher = new Hasher();
        this._oKey = new WordArray([959747464, 1115772636, 691731609, 1915917467, -493200747, -1637910614, -1651049290, -1671095202, 1549556828, 1549556828, 1549556828, 1549556828, 1549556828, 1549556828, 1549556828, 1549556828], 64);
    }

    reset() {
        var e = this._hasher;
        e.reset(),
        e.update(this._iKey)
    }

    update(e) {
        return this._hasher.update(e),
        this
    }

    finalize(e) {
        var t = this._hasher
          , n = t.finalize(e);
        return t.reset(),
        t.finalize(this._oKey.clone().concat(n))
    }
}


function getAuthorization(e, x="") {
    let hasher = new Hasher();
    hasher.reset();
    key = hasher.finalize(x).toString();
    e = `${e}\n${key}`
    let hmac = new HMAC();
    return `YH ${hmac.finalize(e).toString()}`;
}


// let h = new Hasher();
// h.reset();
// key = h.finalize("{\"x\":132}").toString();

// e = `POST
// captcha.pandadastudio.com
// /apis/v1/tokens/0dbdaafe-58da-4808-a202-d2fa0b30219e/validate

// x-yh-appid:356959
// x-yh-date:20250219T100142Z
// x-yh-nonce:l40DN2MePXt4hzO+jkCM5Q==
// x-yh-traceid:YG1xoKPEemXbYnPgT/nrmA==
// ${key}`

// let h1 = new HMAC();
// console.log(`YH ${h1.finalize(e).toString()}`);