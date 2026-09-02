const LoginPage={
  render(){
    return `
<div class="login-page-new">
  <section class="login-left">
    <div class="login-left-inner">
      <div style="margin-bottom: 32px;">
        <h1 class="animate-up delay-1" style="font-size: 2.5rem; font-weight: 600; color: #fff; letter-spacing:-0.02em;">Welcome</h1>
        <p class="animate-up delay-2" style="color: rgba(255,255,255,0.6); margin-top: 8px; font-size: 0.95rem;">Access your account and continue your journey with us</p>
      </div>

      <form class="login-form" id="login-form">
        <div class="animate-up delay-3" style="display:flex;flex-direction:column;gap:8px">
          <label class="login-label" style="text-transform:none; letter-spacing:0; font-size:0.8rem; font-weight:500;">Email Address</label>
          <div class="glass-input-wrapper">
             <input class="glass-input" type="email" id="login-email" value="alicia@sentinel.ai" placeholder="Enter your email address">
          </div>
        </div>
        <div class="animate-up delay-4" style="display:flex;flex-direction:column;gap:8px">
          <label class="login-label" style="text-transform:none; letter-spacing:0; font-size:0.8rem; font-weight:500;">Password</label>
          <div class="glass-input-wrapper" style="position:relative;">
             <input class="glass-input" type="password" id="login-pw" value="sentinel2025" placeholder="Enter your password">
          </div>
        </div>
        <div class="animate-up delay-5 login-options" style="display:flex; justify-content:space-between; align-items:center; margin-top:8px;">
          <label style="display:flex; align-items:center; gap:8px; font-size:0.8rem; color:rgba(255,255,255,0.8); cursor:pointer;">
             <input type="checkbox" checked style="accent-color: var(--blue);"> Keep me signed in
          </label>
          <a href="#" style="font-size:0.8rem; color: #a78bfa; text-decoration:none;">Reset password</a>
        </div>
        <button type="submit" class="login-btn animate-up delay-6" style="margin-top:16px; padding: 14px; font-size: 0.95rem; border-radius: 12px;">Sign In</button>
      </form>

      <div class="login-divider animate-up delay-7">
         <span>Or continue with</span>
      </div>

      <button class="google-btn animate-up delay-8">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">
            <path fill="#FFC107" d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8-6.627 0-12-5.373-12-12s12-5.373 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 12.955 4 4 12.955 4 24s8.955 20 20 20 20-8.955 20-20c0-2.641-.21-5.236-.611-7.743z" />
            <path fill="#FF3D00" d="M6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4 16.318 4 9.656 8.337 6.306 14.691z" />
            <path fill="#4CAF50" d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238C29.211 35.091 26.715 36 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z" />
            <path fill="#1976D2" d="M43.611 20.083H42V20H24v8h11.303c-.792 2.237-2.231 4.166-4.087 5.571l6.19 5.238C42.022 35.026 44 30.038 44 24c0-2.641-.21-5.236-.611-7.743z" />
        </svg>
        Continue with Google
      </button>

      <div class="login-footer animate-up delay-9" style="margin-top:24px; text-align:center;">
        <span style="color: rgba(255,255,255,0.6); font-size: 0.85rem;">New to our platform?</span> 
        <a href="#" style="color: #a78bfa; font-size: 0.85rem; margin-left:4px;">Create Account</a>
      </div>
    </div>
  </section>

  <section class="login-right animate-slide-right delay-3">
    <div class="login-right-bg" style="background-image: url('https://images.unsplash.com/photo-1642615835477-d303d7dc9ee9?w=2160&q=80');"></div>
    
    <div class="testimonials">
      <div class="testimonial-card animate-up delay-8">
        <img src="https://images.unsplash.com/photo-1544005313-94ddf0286df2?q=80&w=150&auto=format&fit=crop" alt="avatar" />
        <div class="t-text">
          <div class="t-name">Sarah Chen</div>
          <div class="t-handle">@sarahdigital</div>
          <div class="t-quote">Amazing platform! The user experience is seamless and the features are exactly what I needed.</div>
        </div>
      </div>
      
      <div class="testimonial-card animate-up delay-9 hidden-md">
        <img src="https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?q=80&w=150&auto=format&fit=crop" alt="avatar" />
        <div class="t-text">
          <div class="t-name">Marcus Johnson</div>
          <div class="t-handle">@marcustech</div>
          <div class="t-quote">This service has transformed how I work. Clean design, powerful features, and excellent support.</div>
        </div>
      </div>
    </div>
  </section>
</div>
`;
  },
  mount(){
    const f=document.getElementById('login-form');
    if(f) f.addEventListener('submit',e=>{e.preventDefault();location.hash='#/overview'});
  }
};
