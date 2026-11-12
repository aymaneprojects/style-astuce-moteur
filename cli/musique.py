# Musique originale synthétisée (aucun échantillon externe), 120 BPM. Libre de droits : composée par ce script.
import numpy as np, wave
def generer(total_frames, sortie, fps=30):
    SR=48000; dur=total_frames/fps+0.3
    N=int(SR*dur); t=np.arange(N)/SR
    L=np.zeros(N); R=np.zeros(N)
    beat=0.5
    def env(n,a=0.01,d=0.3,s=0.6,r=0.5,hold=None):
        x=np.arange(n)/SR; e=np.ones(n)*s
        e[x<a]=x[x<a]/a
        m=(x>=a)&(x<a+d); e[m]=1-(1-s)*(x[m]-a)/d
        if hold is not None:
            m=x>hold; e[m]=s*np.exp(-(x[m]-hold)/r*3)
        return e
    def add(sig,start,gainL=1,gainR=1):
        i=int(start*SR); n=min(len(sig),N-i)
        if n<=0: return
        L[i:i+n]+=sig[:n]*gainL; R[i:i+n]+=sig[:n]*gainR
    def note(f,length,amp):
        n=int(length*SR); x=np.arange(n)/SR
        s=sum(a*np.sin(2*np.pi*f*h*x+ph) for h,a,ph in [(1,1,0),(2,.35,.3),(3,.12,.7),(4,.05,1.1)])
        trem=1+0.08*np.sin(2*np.pi*4.5*x)
        return s*trem*env(n,0.02,0.4,0.55,0.6,hold=length-0.35)*amp
    m=lambda midi:440*2**((midi-69)/12)
    chords=[[53,57,60,64],[52,55,59,62],[50,53,57,60],[48,52,55,59]]  # Fmaj7 Em7 Dm7 Cmaj7
    roots=[41,40,38,36]
    bar=2.0
    for b in range(int(dur/bar)+1):
        c=chords[b%4]; st=b*bar
        for k,mi in enumerate(c):
            add(note(m(mi),bar+0.3,0.055),st+0.012*k,0.9 if k%2 else 1.1,1.1 if k%2 else 0.9)
        # bass
        for off,l in [(0,0.9),(1.25,0.6)]:
            n=int(l*SR); x=np.arange(n)/SR
            add(np.sin(2*np.pi*m(roots[b%4])*x)*env(n,0.01,0.2,0.7,0.2,hold=l-0.15)*0.16,st+off)
        # arpège léger sur les croches de la 2e moitié
        for j in range(4):
            mi=c[(j+b)%4]+12; add(note(m(mi),0.35,0.03),st+1.0+j*0.25,0.7,1.3)
    rng=np.random.default_rng(7)
    for k in range(int(dur/beat)+1):
        st=k*beat
        if k%2==0:  # kick doux sur les temps 1 et 3
            n=int(0.35*SR); x=np.arange(n)/SR; f=50+70*np.exp(-x*30)
            add(np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-x*9)*0.30,st)
        # charleston sur les contretemps
        n=int(0.06*SR); nz=rng.standard_normal(n); nz=np.diff(np.concatenate([[0],nz]))
        add(nz*np.exp(-np.arange(n)/SR*60)*0.035,st+0.25,0.8,1.2)
        if k%4==2:  # clap feutré
            n=int(0.18*SR); nz=rng.standard_normal(n)
            add(np.convolve(nz,np.ones(6)/6,'same')*np.exp(-np.arange(n)/SR*22)*0.07,st)
    # fondu de fin et micro attaque
    fade=np.ones(N); fl=int(1.2*SR); fade[-fl:]=np.linspace(1,0,fl); fade[:int(0.01*SR)]=np.linspace(0,1,int(0.01*SR))
    L*=fade; R*=fade
    st=np.stack([L,R],1); st/=np.abs(st).max()/0.7
    with wave.open(sortie,'wb') as w:
        w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st*32767).astype('<i2').tobytes())
    return dur
