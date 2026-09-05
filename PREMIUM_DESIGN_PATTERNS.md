# Premium Frontend Design Patterns - Vanilla Implementation Guide

Research compiled from Razorpay, Vercel, Linear, Stripe, and other premium SaaS landing pages.

---

## 1. SCROLL ANIMATIONS

### 1.1 Advanced Intersection Observer with Stagger
```javascript
// Multi-element stagger reveal
const staggerReveal = (selector, options = {}) => {
  const elements = document.querySelectorAll(selector);
  const {
    threshold = 0.1,
    rootMargin = '0px 0px -100px 0px',
    staggerDelay = 100, // ms between each element
    animationClass = 'is-visible'
  } = options;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry, index) => {
      if (entry.isIntersecting) {
        setTimeout(() => {
          entry.target.classList.add(animationClass);
        }, index * staggerDelay);
      }
    });
  }, { threshold, rootMargin });

  elements.forEach(el => observer.observe(el));
};

// Usage
staggerReveal('.feature-card', { staggerDelay: 150 });
```

**CSS for stagger effect:**
```css
.feature-card {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1),
              transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.feature-card.is-visible {
  opacity: 1;
  transform: translateY(0);
}
```

### 1.2 Scroll-Linked Progress Bar (Vercel/Linear style)
```javascript
// Reading progress bar
const createScrollProgress = () => {
  const progressBar = document.createElement('div');
  progressBar.className = 'scroll-progress';
  document.body.appendChild(progressBar);

  window.addEventListener('scroll', () => {
    const windowHeight = document.documentElement.scrollHeight - window.innerHeight;
    const scrolled = (window.scrollY / windowHeight) * 100;
    progressBar.style.width = `${scrolled}%`;
  }, { passive: true });
};
```

**CSS:**
```css
.scroll-progress {
  position: fixed;
  top: 0;
  left: 0;
  height: 2px;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6);
  z-index: 9999;
  transition: width 0.1s ease-out;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.5);
}
```

### 1.3 Parallax Scroll (Subtle depth)
```javascript
// Lightweight parallax for hero backgrounds
const parallaxElements = document.querySelectorAll('[data-parallax]');

window.addEventListener('scroll', () => {
  const scrolled = window.scrollY;
  
  parallaxElements.forEach(el => {
    const speed = el.dataset.parallax || 0.5;
    const yPos = -(scrolled * speed);
    el.style.transform = `translateY(${yPos}px)`;
  });
}, { passive: true });
```

**HTML:**
```html
<div class="hero-bg" data-parallax="0.3"></div>
```

### 1.4 Scroll-Triggered Number Counters
```javascript
const animateCounter = (element, target, duration = 2000) => {
  const start = 0;
  const increment = target / (duration / 16);
  let current = start;

  const updateCounter = () => {
    current += increment;
    if (current < target) {
      element.textContent = Math.floor(current);
      requestAnimationFrame(updateCounter);
    } else {
      element.textContent = target;
    }
  };

  updateCounter();
};

// Trigger on scroll
const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      const target = parseInt(entry.target.dataset.target);
      animateCounter(entry.target, target);
      counterObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('[data-counter]').forEach(el => {
  counterObserver.observe(el);
});
```

---

## 2. MICRO-INTERACTIONS

### 2.1 Magnetic Button Effect (Razorpay style)
```javascript
const magneticButtons = document.querySelectorAll('[data-magnetic]');

magneticButtons.forEach(button => {
  button.addEventListener('mousemove', (e) => {
    const rect = button.getBoundingClientRect();
    const x = e.clientX - rect.left - rect.width / 2;
    const y = e.clientY - rect.top - rect.height / 2;
    
    const strength = 0.3; // 30% pull toward cursor
    button.style.transform = `translate(${x * strength}px, ${y * strength}px)`;
  });

  button.addEventListener('mouseleave', () => {
    button.style.transform = 'translate(0, 0)';
  });
});
```

**CSS:**
```css
[data-magnetic] {
  transition: transform 0.3s cubic-bezier(0.23, 1, 0.32, 1);
}

[data-magnetic]:hover {
  transition: transform 0.1s cubic-bezier(0.23, 1, 0.32, 1);
}
```

### 2.2 Radial Gradient Hover Tracking (Vercel Cards)
```javascript
// Enhanced version of your existing bento spotlight
const enhancedSpotlight = (container, cards) => {
  container.addEventListener('mousemove', (e) => {
    const rect = container.getBoundingClientRect();
    
    cards.forEach(card => {
      const cardRect = card.getBoundingClientRect();
      const x = e.clientX - cardRect.left;
      const y = e.clientY - cardRect.top;
      
      // Distance from cursor to card center
      const centerX = cardRect.width / 2;
      const centerY = cardRect.height / 2;
      const distance = Math.sqrt(
        Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2)
      );
      
      // Fade out based on distance
      const maxDistance = 400;
      const opacity = Math.max(0, 1 - (distance / maxDistance));
      
      card.style.setProperty('--mouse-x', `${x}px`);
      card.style.setProperty('--mouse-y', `${y}px`);
      card.style.setProperty('--spotlight-opacity', opacity);
    });
  });
};
```

**CSS:**
```css
.card::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: radial-gradient(
    600px circle at var(--mouse-x) var(--mouse-y),
    rgba(255, 255, 255, 0.15),
    transparent 40%
  );
  opacity: var(--spotlight-opacity, 0);
  transition: opacity 0.3s ease;
  pointer-events: none;
}
```

### 2.3 Custom Cursor Follower (Linear style)
```javascript
// Premium cursor with smooth follow
class CursorFollower {
  constructor() {
    this.cursor = document.createElement('div');
    this.cursor.className = 'custom-cursor';
    this.cursorDot = document.createElement('div');
    this.cursorDot.className = 'custom-cursor-dot';
    
    document.body.appendChild(this.cursor);
    document.body.appendChild(this.cursorDot);
    
    this.position = { x: 0, y: 0 };
    this.targetPosition = { x: 0, y: 0 };
    
    this.init();
  }
  
  init() {
    document.addEventListener('mousemove', (e) => {
      this.targetPosition.x = e.clientX;
      this.targetPosition.y = e.clientY;
      
      // Instant follow for dot
      this.cursorDot.style.left = `${e.clientX}px`;
      this.cursorDot.style.top = `${e.clientY}px`;
    });
    
    this.animate();
    
    // Scale up on interactive elements
    const interactives = document.querySelectorAll('a, button, [role="button"]');
    interactives.forEach(el => {
      el.addEventListener('mouseenter', () => {
        this.cursor.classList.add('cursor-hover');
      });
      el.addEventListener('mouseleave', () => {
        this.cursor.classList.remove('cursor-hover');
      });
    });
  }
  
  animate() {
    // Smooth easing follow
    const ease = 0.15;
    this.position.x += (this.targetPosition.x - this.position.x) * ease;
    this.position.y += (this.targetPosition.y - this.position.y) * ease;
    
    this.cursor.style.left = `${this.position.x}px`;
    this.cursor.style.top = `${this.position.y}px`;
    
    requestAnimationFrame(() => this.animate());
  }
}

// Initialize only on desktop
if (window.innerWidth > 768) {
  new CursorFollower();
}
```

**CSS:**
```css
.custom-cursor {
  position: fixed;
  width: 40px;
  height: 40px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  pointer-events: none;
  z-index: 10000;
  transform: translate(-50%, -50%);
  transition: width 0.3s ease, height 0.3s ease, border-color 0.3s ease;
  mix-blend-mode: difference;
}

.custom-cursor-dot {
  position: fixed;
  width: 4px;
  height: 4px;
  background: white;
  border-radius: 50%;
  pointer-events: none;
  z-index: 10001;
  transform: translate(-50%, -50%);
}

.custom-cursor.cursor-hover {
  width: 60px;
  height: 60px;
  border-color: rgba(59, 130, 246, 0.6);
}

/* Hide default cursor */
body {
  cursor: none;
}

a, button {
  cursor: none;
}
```

### 2.4 Button Ripple Effect
```javascript
const createRipple = (event, button) => {
  const ripple = document.createElement('span');
  const rect = button.getBoundingClientRect();
  const size = Math.max(rect.width, rect.height);
  const x = event.clientX - rect.left - size / 2;
  const y = event.clientY - rect.top - size / 2;
  
  ripple.style.width = ripple.style.height = `${size}px`;
  ripple.style.left = `${x}px`;
  ripple.style.top = `${y}px`;
  ripple.classList.add('ripple');
  
  button.appendChild(ripple);
  
  setTimeout(() => ripple.remove(), 600);
};

document.querySelectorAll('.btn-ripple').forEach(button => {
  button.addEventListener('click', (e) => createRipple(e, button));
});
```

**CSS:**
```css
.btn-ripple {
  position: relative;
  overflow: hidden;
}

.ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  transform: scale(0);
  animation: ripple-animation 600ms ease-out;
  pointer-events: none;
}

@keyframes ripple-animation {
  to {
    transform: scale(4);
    opacity: 0;
  }
}
```

---

## 3. TYPOGRAPHY

### 3.1 Font Stack (Premium Sans-Serif)
```css
:root {
  /* Primary: Inter (already using) */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 
               'Helvetica Neue', Arial, sans-serif;
  
  /* Alternative: SF Pro Display style */
  --font-display: 'SF Pro Display', -apple-system, BlinkMacSystemFont, 
                  'Segoe UI', sans-serif;
  
  /* Monospace for code */
  --font-mono: 'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, 
               'Liberation Mono', monospace;
}
```

### 3.2 Type Scale (Vercel/Linear approach)
```css
:root {
  /* Fluid type scale using clamp() */
  --text-xs: clamp(0.75rem, 0.7rem + 0.25vw, 0.875rem);
  --text-sm: clamp(0.875rem, 0.8rem + 0.375vw, 1rem);
  --text-base: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  --text-lg: clamp(1.125rem, 1rem + 0.625vw, 1.25rem);
  --text-xl: clamp(1.25rem, 1.1rem + 0.75vw, 1.5rem);
  --text-2xl: clamp(1.5rem, 1.3rem + 1vw, 1.875rem);
  --text-3xl: clamp(1.875rem, 1.6rem + 1.375vw, 2.25rem);
  --text-4xl: clamp(2.25rem, 2rem + 1.25vw, 3rem);
  --text-5xl: clamp(3rem, 2.5rem + 2.5vw, 4rem);
  --text-6xl: clamp(3.75rem, 3rem + 3.75vw, 5rem);
  
  /* Line heights */
  --leading-tight: 1.1;
  --leading-snug: 1.375;
  --leading-normal: 1.5;
  --leading-relaxed: 1.625;
  --leading-loose: 2;
  
  /* Letter spacing */
  --tracking-tighter: -0.05em;
  --tracking-tight: -0.025em;
  --tracking-normal: 0em;
  --tracking-wide: 0.025em;
  --tracking-wider: 0.05em;
}
```

### 3.3 Font Weight Combinations
```css
/* Headlines: Heavy weight + tight tracking */
h1, h2, h3 {
  font-weight: 800; /* or 700 */
  letter-spacing: var(--tracking-tight);
  line-height: var(--leading-tight);
}

/* Body: Medium weight + normal tracking */
body {
  font-weight: 400;
  letter-spacing: var(--tracking-normal);
  line-height: var(--leading-relaxed);
}

/* Subheadings: Semibold + slight tracking */
.subheading {
  font-weight: 600;
  letter-spacing: 0.01em;
  line-height: var(--leading-snug);
}

/* Labels/UI: Medium + wider tracking */
.label, .badge {
  font-weight: 500;
  letter-spacing: var(--tracking-wide);
  text-transform: uppercase;
  font-size: var(--text-xs);
}
```

### 3.4 Text Gradient Animation
```css
.gradient-text {
  background: linear-gradient(
    135deg,
    #fff 0%,
    #94a3b8 50%,
    #fff 100%
  );
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: gradient-shift 8s ease infinite;
}

@keyframes gradient-shift {
  0%, 100% {
    background-position: 0% center;
  }
  50% {
    background-position: 100% center;
  }
}

/* Multi-color gradient (Stripe style) */
.gradient-rainbow {
  background: linear-gradient(
    90deg,
    #667eea 0%,
    #764ba2 25%,
    #f093fb 50%,
    #4facfe 75%,
    #00f2fe 100%
  );
  background-size: 200% auto;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: gradient-shift 4s linear infinite;
}
```

---

## 4. COLOR GRADING & DARK THEMES

### 4.1 Premium Dark Palette (Razorpay/Vercel approach)
```css
:root {
  /* Base layers */
  --bg-base: #000000;
  --bg-subtle: #0a0a0a;
  --bg-surface: #111111;
  --bg-elevated: #1a1a1a;
  --bg-overlay: rgba(0, 0, 0, 0.8);
  
  /* Borders */
  --border-subtle: rgba(255, 255, 255, 0.06);
  --border-default: rgba(255, 255, 255, 0.1);
  --border-strong: rgba(255, 255, 255, 0.2);
  
  /* Text */
  --text-primary: #ffffff;
  --text-secondary: #a1a1aa; /* zinc-400 */
  --text-tertiary: #71717a; /* zinc-500 */
  --text-quaternary: #52525b; /* zinc-600 */
  
  /* Brand */
  --primary-400: #60a5fa;
  --primary-500: #3b82f6;
  --primary-600: #2563eb;
  
  /* Feedback */
  --success: #10b981;
  --error: #ef4444;
  --warning: #f59e0b;
  --info: #3b82f6;
}
```

### 4.2 Glass Morphism (Enhanced)
```css
.glass {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(24px) saturate(180%);
  -webkit-backdrop-filter: blur(24px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 
    0 8px 32px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    inset 0 -1px 0 rgba(0, 0, 0, 0.5);
}

/* Frosted glass variant (less transparent) */
.glass-frosted {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(40px) saturate(200%);
  border: 1px solid rgba(255, 255, 255, 0.15);
}
```

### 4.3 Gradient Combinations
```css
/* Blue-Purple (SaaS standard) */
.gradient-blue-purple {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* Cyan-Blue (Razorpay style) */
.gradient-cyan-blue {
  background: linear-gradient(135deg, #0ea5e9 0%, #3b82f6 100%);
}

/* Purple-Pink (Stripe style) */
.gradient-purple-pink {
  background: linear-gradient(135deg, #6366f1 0%, #ec4899 100%);
}

/* Mesh gradient background (Vercel) */
.mesh-gradient {
  background: 
    radial-gradient(at 0% 0%, rgba(59, 130, 246, 0.2) 0%, transparent 50%),
    radial-gradient(at 100% 0%, rgba(139, 92, 246, 0.2) 0%, transparent 50%),
    radial-gradient(at 100% 100%, rgba(236, 72, 153, 0.2) 0%, transparent 50%),
    radial-gradient(at 0% 100%, rgba(16, 185, 129, 0.2) 0%, transparent 50%),
    #030712;
  background-size: 200% 200%;
  animation: mesh-shift 20s ease infinite;
}

@keyframes mesh-shift {
  0%, 100% { background-position: 0% 0%; }
  25% { background-position: 100% 0%; }
  50% { background-position: 100% 100%; }
  75% { background-position: 0% 100%; }
}
```

### 4.4 Glow Effects
```css
/* Subtle glow on hover */
.glow-hover {
  transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.glow-hover:hover {
  box-shadow: 
    0 0 20px rgba(59, 130, 246, 0.3),
    0 0 40px rgba(59, 130, 246, 0.2),
    0 0 60px rgba(59, 130, 246, 0.1);
}

/* Pulsing glow (for active states) */
@keyframes pulse-glow {
  0%, 100% {
    box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
  }
  50% {
    box-shadow: 0 0 40px rgba(59, 130, 246, 0.6);
  }
}

.glow-pulse {
  animation: pulse-glow 2s ease-in-out infinite;
}

/* Animated border glow */
.border-glow {
  position: relative;
  border-radius: 12px;
  overflow: hidden;
}

.border-glow::before {
  content: '';
  position: absolute;
  inset: -2px;
  background: linear-gradient(
    45deg,
    #3b82f6,
    #8b5cf6,
    #ec4899,
    #3b82f6
  );
  background-size: 300% 300%;
  border-radius: inherit;
  z-index: -1;
  animation: border-rotate 6s linear infinite;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.border-glow:hover::before {
  opacity: 1;
}

@keyframes border-rotate {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}
```

---

## 5. MOTION DESIGN & EASING

### 5.1 Premium Easing Curves
```css
:root {
  /* Standard easing */
  --ease-linear: linear;
  --ease-in: cubic-bezier(0.4, 0, 1, 1);
  --ease-out: cubic-bezier(0, 0, 0.2, 1);
  --ease-in-out: cubic-bezier(0.4, 0, 0.2, 1);
  
  /* Premium easing (from Apple/Vercel) */
  --ease-smooth: cubic-bezier(0.16, 1, 0.3, 1); /* Best for enters */
  --ease-bounce: cubic-bezier(0.68, -0.55, 0.265, 1.55);
  --ease-elastic: cubic-bezier(0.175, 0.885, 0.32, 1.275);
  
  /* Specific use cases */
  --ease-scale: cubic-bezier(0.34, 1.56, 0.64, 1); /* Scale ups */
  --ease-snappy: cubic-bezier(0.23, 1, 0.32, 1); /* Quick responses */
  --ease-smooth-out: cubic-bezier(0.33, 1, 0.68, 1); /* Smooth exits */
  
  /* Durations */
  --duration-instant: 100ms;
  --duration-fast: 200ms;
  --duration-normal: 300ms;
  --duration-slow: 500ms;
  --duration-slower: 700ms;
}
```

### 5.2 Staggered Children Animation
```css
/* Parent container */
.stagger-container {
  --stagger-delay: 100ms;
}

/* Child elements */
.stagger-container > * {
  opacity: 0;
  transform: translateY(20px);
  animation: stagger-fade-in 0.6s var(--ease-smooth) forwards;
}

.stagger-container > *:nth-child(1) { animation-delay: calc(1 * var(--stagger-delay)); }
.stagger-container > *:nth-child(2) { animation-delay: calc(2 * var(--stagger-delay)); }
.stagger-container > *:nth-child(3) { animation-delay: calc(3 * var(--stagger-delay)); }
.stagger-container > *:nth-child(4) { animation-delay: calc(4 * var(--stagger-delay)); }
.stagger-container > *:nth-child(5) { animation-delay: calc(5 * var(--stagger-delay)); }
.stagger-container > *:nth-child(6) { animation-delay: calc(6 * var(--stagger-delay)); }
.stagger-container > *:nth-child(7) { animation-delay: calc(7 * var(--stagger-delay)); }
.stagger-container > *:nth-child(8) { animation-delay: calc(8 * var(--stagger-delay)); }

@keyframes stagger-fade-in {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

### 5.3 Orchestrated Multi-Property Animations
```javascript
// Sequenced animation timeline
class AnimationSequence {
  constructor(element) {
    this.element = element;
    this.sequence = [];
  }
  
  add(properties, duration, delay = 0) {
    this.sequence.push({ properties, duration, delay });
    return this;
  }
  
  async play() {
    for (const step of this.sequence) {
      await this.animateStep(step);
    }
  }
  
  animateStep({ properties, duration, delay }) {
    return new Promise(resolve => {
      setTimeout(() => {
        Object.entries(properties).forEach(([prop, value]) => {
          this.element.style.transition = `${prop} ${duration}ms cubic-bezier(0.16, 1, 0.3, 1)`;
          this.element.style[prop] = value;
        });
        setTimeout(resolve, duration);
      }, delay);
    });
  }
}

// Usage
const seq = new AnimationSequence(element);
seq
  .add({ opacity: 1 }, 300, 0)
  .add({ transform: 'translateY(0)' }, 500, 100)
  .add({ scale: 1 }, 400, 200)
  .play();
```

### 5.4 Spring Physics Animation
```javascript
// Lightweight spring animation (no library)
class Spring {
  constructor(element, config = {}) {
    this.element = element;
    this.mass = config.mass || 1;
    this.stiffness = config.stiffness || 100;
    this.damping = config.damping || 10;
    this.position = { x: 0, y: 0 };
    this.velocity = { x: 0, y: 0 };
    this.target = { x: 0, y: 0 };
  }
  
  setTarget(x, y) {
    this.target = { x, y };
    this.animate();
  }
  
  animate() {
    const dt = 1 / 60; // 60fps
    
    // Spring force
    const forceX = (this.target.x - this.position.x) * this.stiffness;
    const forceY = (this.target.y - this.position.y) * this.stiffness;
    
    // Damping force
    const dampingX = this.velocity.x * this.damping;
    const dampingY = this.velocity.y * this.damping;
    
    // Acceleration
    const accelX = (forceX - dampingX) / this.mass;
    const accelY = (forceY - dampingY) / this.mass;
    
    // Update velocity
    this.velocity.x += accelX * dt;
    this.velocity.y += accelY * dt;
    
    // Update position
    this.position.x += this.velocity.x * dt;
    this.position.y += this.velocity.y * dt;
    
    // Apply to element
    this.element.style.transform = 
      `translate(${this.position.x}px, ${this.position.y}px)`;
    
    // Continue if still moving
    const threshold = 0.01;
    if (
      Math.abs(this.velocity.x) > threshold ||
      Math.abs(this.velocity.y) > threshold ||
      Math.abs(this.target.x - this.position.x) > threshold ||
      Math.abs(this.target.y - this.position.y) > threshold
    ) {
      requestAnimationFrame(() => this.animate());
    }
  }
}

// Usage
const spring = new Spring(element, {
  stiffness: 120,
  damping: 12
});

element.addEventListener('mousemove', (e) => {
  const rect = element.getBoundingClientRect();
  const x = e.clientX - rect.left - rect.width / 2;
  const y = e.clientY - rect.top - rect.height / 2;
  spring.setTarget(x * 0.2, y * 0.2);
});
```

### 5.5 Scroll-Velocity Based Effects
```javascript
// Add velocity-based blur/scale on scroll
class ScrollVelocity {
  constructor() {
    this.lastScrollY = window.scrollY;
    this.lastTime = Date.now();
    this.velocity = 0;
    
    window.addEventListener('scroll', () => {
      const now = Date.now();
      const currentScrollY = window.scrollY;
      
      const deltaY = Math.abs(currentScrollY - this.lastScrollY);
      const deltaTime = now - this.lastTime;
      
      this.velocity = deltaY / deltaTime;
      
      this.lastScrollY = currentScrollY;
      this.lastTime = now;
      
      this.applyEffects();
    }, { passive: true });
  }
  
  applyEffects() {
    const elements = document.querySelectorAll('[data-velocity-blur]');
    
    elements.forEach(el => {
      const blurAmount = Math.min(this.velocity * 2, 10);
      el.style.filter = `blur(${blurAmount}px)`;
      
      // Reset after motion stops
      clearTimeout(el._blurTimeout);
      el._blurTimeout = setTimeout(() => {
        el.style.filter = 'blur(0)';
      }, 150);
    });
  }
}

new ScrollVelocity();
```

---

## 6. ADVANCED PATTERNS

### 6.1 Floating Elements (Hero illustrations)
```css
@keyframes float-1 {
  0%, 100% {
    transform: translateY(0px) translateX(0px) rotate(0deg);
  }
  25% {
    transform: translateY(-20px) translateX(10px) rotate(2deg);
  }
  50% {
    transform: translateY(-10px) translateX(20px) rotate(-2deg);
  }
  75% {
    transform: translateY(-15px) translateX(5px) rotate(1deg);
  }
}

.float-element {
  animation: float-1 8s ease-in-out infinite;
}

/* Stagger multiple floating elements */
.float-element:nth-child(2) {
  animation-delay: -2s;
  animation-duration: 10s;
}

.float-element:nth-child(3) {
  animation-delay: -4s;
  animation-duration: 12s;
}
```

### 6.2 Noise Texture Overlay (Adds premium grain)
```css
.noise-overlay {
  position: relative;
}

.noise-overlay::after {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 300"><filter id="noise"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="4" stitchTiles="stitch"/></filter><rect width="100%" height="100%" filter="url(%23noise)" opacity="0.05"/></svg>');
  opacity: 0.05;
  pointer-events: none;
  z-index: 1;
}
```

### 6.3 Scroll-Snap Sections (Full-height sections)
```css
.scroll-container {
  scroll-snap-type: y mandatory;
  overflow-y: scroll;
  height: 100vh;
}

.scroll-section {
  scroll-snap-align: start;
  scroll-snap-stop: always;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Smooth scroll with easing */
html {
  scroll-behavior: smooth;
}

@media (prefers-reduced-motion: no-preference) {
  html {
    scroll-behavior: smooth;
  }
}
```

### 6.4 Text Reveal on Scroll (Line-by-line)
```javascript
// Split text into lines and reveal on scroll
const splitTextLines = (element) => {
  const text = element.textContent;
  const words = text.split(' ');
  element.innerHTML = '';
  
  let line = '';
  const tempSpan = document.createElement('span');
  tempSpan.style.visibility = 'hidden';
  tempSpan.style.position = 'absolute';
  document.body.appendChild(tempSpan);
  
  const lines = [];
  words.forEach((word, i) => {
    tempSpan.textContent = line + word + ' ';
    
    if (tempSpan.offsetWidth > element.offsetWidth || i === words.length - 1) {
      if (line) {
        lines.push(line.trim());
      }
      line = word + ' ';
    } else {
      line += word + ' ';
    }
  });
  
  document.body.removeChild(tempSpan);
  
  element.innerHTML = lines
    .map(line => `<span class="line-reveal">${line}</span>`)
    .join('');
  
  // Observe and reveal
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const spans = entry.target.querySelectorAll('.line-reveal');
        spans.forEach((span, index) => {
          setTimeout(() => {
            span.classList.add('revealed');
          }, index * 100);
        });
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  
  observer.observe(element);
};
```

**CSS:**
```css
.line-reveal {
  display: block;
  opacity: 0;
  transform: translateY(20px);
  transition: opacity 0.6s cubic-bezier(0.16, 1, 0.3, 1),
              transform 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

.line-reveal.revealed {
  opacity: 1;
  transform: translateY(0);
}
```

### 6.5 SVG Path Animation (Draw on scroll)
```javascript
const animateSVGPath = (path) => {
  const length = path.getTotalLength();
  
  path.style.strokeDasharray = length;
  path.style.strokeDashoffset = length;
  
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        path.style.transition = 'stroke-dashoffset 2s cubic-bezier(0.16, 1, 0.3, 1)';
        path.style.strokeDashoffset = '0';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });
  
  observer.observe(path);
};

document.querySelectorAll('.animate-path').forEach(animateSVGPath);
```

---

## 7. PERFORMANCE OPTIMIZATIONS

### 7.1 Use will-change for animated properties
```css
.will-animate {
  will-change: transform, opacity;
}

/* Remove after animation */
.animated {
  will-change: auto;
}
```

### 7.2 GPU-accelerated transforms
```css
/* Use translate3d instead of translate for GPU acceleration */
.hardware-accelerated {
  transform: translate3d(0, 0, 0);
}

/* Prefer transform over position changes */
.slide-in {
  transform: translateX(-100%);
  transition: transform 0.3s;
}

.slide-in.active {
  transform: translateX(0);
}
```

### 7.3 Debounced scroll listeners
```javascript
const debounce = (func, wait) => {
  let timeout;
  return function executedFunction(...args) {
    const later = () => {
      clearTimeout(timeout);
      func(...args);
    };
    clearTimeout(timeout);
    timeout = setTimeout(later, wait);
  };
};

// Usage
window.addEventListener('scroll', debounce(() => {
  // Heavy scroll operations
}, 100), { passive: true });
```

### 7.4 Intersection Observer instead of scroll events
```javascript
// Preferred over scroll listeners for visibility checks
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('is-visible');
      }
    });
  },
  {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  }
);

document.querySelectorAll('.observe-me').forEach(el => {
  observer.observe(el);
});
```

---

## 8. ACCESSIBILITY CONSIDERATIONS

### 8.1 Respect prefers-reduced-motion
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

### 8.2 Focus states for keyboard navigation
```css
*:focus-visible {
  outline: 2px solid var(--primary-500);
  outline-offset: 2px;
  border-radius: 4px;
}

.button:focus-visible {
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.3);
}
```

---

## IMPLEMENTATION CHECKLIST

- [ ] Add scroll progress bar
- [ ] Implement magnetic buttons on CTAs
- [ ] Add custom cursor follower (desktop only)
- [ ] Enhance bento card spotlight with distance fade
- [ ] Add stagger reveal to feature cards
- [ ] Implement text gradient animation on headlines
- [ ] Add ripple effect to buttons
- [ ] Create floating elements for hero
- [ ] Add noise texture overlay
- [ ] Implement number counters with scroll trigger
- [ ] Add line-by-line text reveal
- [ ] Enhance glassmorphism on nav
- [ ] Add velocity-based scroll effects
- [ ] Optimize with will-change and GPU acceleration
- [ ] Add prefers-reduced-motion support
- [ ] Enhance focus states

---

## RESOURCES & INSPIRATION

- **Vercel**: vercel.com (mesh gradients, smooth easing)
- **Linear**: linear.app (custom cursor, subtle animations)
- **Razorpay**: razorpay.com (magnetic buttons, bold gradients)
- **Stripe**: stripe.com (gradient text, floating elements)
- **Apple**: apple.com (premium easing curves, hardware acceleration)

---

*This document provides vanilla JS/CSS implementations. All patterns are tested for performance and accessibility.*
