// --- Utilities ---
    const qs = (sel, el=document) => el.querySelector(sel);
    const qsa = (sel, el=document) => [...el.querySelectorAll(sel)];

    const toast = (msg, type='info') => {
      const t = document.createElement('div');
      t.className = 'toast-item fade-in';
      t.innerHTML = `<div class="flex items-start gap-3">
        <span class="mt-0.5 h-2.5 w-2.5 rounded-full ${type==='success'?'bg-emerald-400':type==='error'?'bg-rose-400':'bg-indigo-400'}"></span>
        <div class="text-sm">${msg}</div>
      </div>`;
      const wrap = qs('#toaster');
      wrap.appendChild(t);
      setTimeout(() => { t.style.opacity = '0'; t.style.transform = 'translateY(6px)'; }, 3600);
      setTimeout(() => t.remove(), 4200);
    };

    const storage = {
      getUsers(){
        try { return JSON.parse(localStorage.getItem('users')||'{}'); } catch { return {}; }
      },
      setUsers(users){ localStorage.setItem('users', JSON.stringify(users)); },
      setSession(email, remember){
        const payload = JSON.stringify({ email, remember, lastLogin: Date.now() });
        if(remember){ localStorage.setItem('auth', payload); sessionStorage.removeItem('auth'); }
        else { sessionStorage.setItem('auth', payload); localStorage.removeItem('auth'); }
      },
      getSession(){
        const s = sessionStorage.getItem('auth');
        if(s) return JSON.parse(s);
        const p = localStorage.getItem('auth');
        if(p) return JSON.parse(p);
        return null;
      },
      clearSession(){ sessionStorage.removeItem('auth'); localStorage.removeItem('auth'); }
    };

    const auth = {
      current(){ const s = storage.getSession(); return s?.email || null; },
      isRemembered(){ const s = localStorage.getItem('auth'); return !!s; },
      getUser(){
        const email = auth.current(); if(!email) return null; const users = storage.getUsers(); return users[email] || null;
      },
      register({name, email, password, remember}){
        const users = storage.getUsers();
        const key = email.toLowerCase().trim();
        if(users[key]) throw new Error('Bu e-posta ile bir hesap zaten var.');
        users[key] = { name: name.trim(), email: key, password: String(password), createdAt: Date.now(), about: '' };
        storage.setUsers(users);
        storage.setSession(key, !!remember);
        return users[key];
      },
      login({email, password, remember}){
        const users = storage.getUsers();
        const key = email.toLowerCase().trim();
        const user = users[key];
        if(!user || user.password !== String(password)) throw new Error('E-posta veya şifre hatalı.');
        storage.setSession(key, !!remember);
        const users2 = storage.getUsers();
        users2[key].lastLogin = Date.now();
        storage.setUsers(users2);
        return user;
      },
      logout(){ storage.clearSession(); }
    };

    // --- Routing ---
    const routes = {
      home: () => showView('view-home'),
      auth: () => showView('view-auth'),
      profile: () => { if(!auth.current()) { location.hash = '#/auth'; return; } showView('view-profile'); renderProfile(); }
    };

    function showView(id){
      qsa('main section').forEach(s => s.classList.add('hidden'));
      const el = qs('#'+id);
      if(el){ el.classList.remove('hidden'); el.classList.add('fade-in'); }
      updateHeader();
    }

    function navigate(){
      const h = location.hash.replace('#','');
      if(h.startsWith('/profile')) return routes.profile();
      if(h.startsWith('/auth')) return routes.auth();
      return routes.home();
    }

    // --- UI Binding ---
    function updateHeader(){
      const logged = !!auth.current();
      const btn = qs('#headerPrimaryBtn');
      const btnText = qs('#headerPrimaryBtnText');
      const logoutBtn = qs('#logoutBtn');
      if(logged){
        btnText.textContent = 'Profilim';
        btn.onclick = () => location.hash = '#/profile';
        logoutBtn.classList.remove('hidden');
      } else {
        btnText.textContent = 'Başla';
        btn.onclick = () => location.hash = '#/auth';
        logoutBtn.classList.add('hidden');
      }
    }

    function bindAuthUI(){
      const tabLogin = qs('#tab-login');
      const tabRegister = qs('#tab-register');
      const formLogin = qs('#form-login');
      const formRegister = qs('#form-register');

      const activate = (mode) => {
        if(mode==='login'){
          tabLogin.classList.add('tab-active'); tabRegister.classList.remove('tab-active');
          formLogin.classList.remove('hidden'); formRegister.classList.add('hidden');
        } else {
          tabRegister.classList.add('tab-active'); tabLogin.classList.remove('tab-active');
          formRegister.classList.remove('hidden'); formLogin.classList.add('hidden');
        }
      };

      tabLogin.onclick = () => activate('login');
      tabRegister.onclick = () => activate('register');

      formLogin.addEventListener('submit', (e) => {
        e.preventDefault();
        const email = qs('#loginEmail').value;
        const password = qs('#loginPassword').value;
        const remember = qs('#loginRemember').checked;
        try{ auth.login({email, password, remember}); toast('Hoş geldin!','success'); window.location.href = 'templates/index.html'; }
        catch(err){ toast(err.message,'error'); }
      });

      formRegister.addEventListener('submit', (e) => {
        e.preventDefault();
        const name = qs('#regName').value;
        const email = qs('#regEmail').value;
        const password = qs('#regPassword').value;
        const password2 = qs('#regPassword2').value;
        const remember = qs('#regRemember').checked;
        if(password !== password2){ toast('Şifreler eşleşmiyor.','error'); return; }
        try{ auth.register({name, email, password, remember}); toast('Kayıt başarılı!','success'); window.location.href = 'templates/index.html'; }
        catch(err){ toast(err.message,'error'); }
      });

      // Header logout buttons
      qs('#logoutBtn').onclick = () => { auth.logout(); toast('Çıkış yapıldı.'); navigate(); };
      qs('#logoutBtn2').onclick = () => { auth.logout(); toast('Çıkış yapıldı.'); location.hash = '#/home'; };

      // Home CTA adjusts by auth state
      const cta = qs('#ctaStart');
      cta.onclick = (e) => {
        if(auth.current()){ e.preventDefault(); window.location.href = 'templates/index.html'; }
      };
    }

    // --- Profile Rendering ---
    async function renderProfile(){
      const user = auth.getUser();
      if(!user) return;
      // Header bits
      qs('#profileName').textContent = user.name || 'Kullanıcı';
      qs('#profileEmail').textContent = user.email;
      qs('#aboutText').textContent = user.about?.trim() || 'Henüz bir bilgi eklenmedi.';
      qs('#avatar').textContent = initials(user.name || user.email);

      const created = user.createdAt ? new Date(user.createdAt) : new Date();
      const days = Math.max(1, Math.ceil((Date.now() - created.getTime()) / 86400000));
      qs('#memberSince').textContent = 'Üyelik: ' + created.toLocaleDateString('tr-TR');
      qs('#daysCount').textContent = String(days);

      const s = storage.getSession();
      const lastLogin = user.lastLogin || s?.lastLogin || user.createdAt;
      qs('#lastLogin').textContent = lastLogin ? new Date(lastLogin).toLocaleString('tr-TR') : '-';

      // Load external profile template or fallback
      await loadProfileTemplate(user, { days, created });

      // Bind edit modal
      bindEditProfile(user);
    }

    function initials(name){
      return (name||'').split(/\s+/).filter(Boolean).slice(0,2).map(s=>s[0]?.toUpperCase()).join('') || 'U';
    }

    async function loadProfileTemplate(user, {days, created}){
      const container = qs('#profileTemplateContainer');
      container.innerHTML = `<div class="text-slate-400">Şablon yükleniyor...</div>`;
      try{
        const res = await fetch('../script/index.html', { cache:'no-store' });
        if(res.ok){
          const html = await res.text();
          if(html && html.trim().length){
            container.innerHTML = html;
            toast('Harici profil şablonu yüklendi.','success');
            console.info('Profil şablonu ../script/index.html adresinden yüklendi.');
            return;
          }
        }
        throw new Error('Boş içerik');
      }catch(err){
        const tpl = qs('#fallbackProfileTemplate').innerHTML;
        const filled = tpl
          .replaceAll('{{name}}', escapeHtml(user.name||''))
          .replaceAll('{{email}}', escapeHtml(user.email||''))
          .replaceAll('{{about}}', escapeHtml(user.about?.trim()||'Henüz bir bilgi eklenmedi.'))
          .replaceAll('{{days}}', String(days))
          .replaceAll('{{createdAt}}', created.toLocaleDateString('tr-TR'))
          .replaceAll('{{initials}}', initials(user.name||user.email));
        container.innerHTML = filled;
        toast('Harici şablon bulunamadı, varsayılan kullanılıyor.');
      }
    }

    function escapeHtml(s){
      return String(s).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;');
    }

    function bindEditProfile(user){
      const modal = qs('#editModal');
      const open = () => { modal.classList.remove('hidden'); qs('#editName').value = user.name||''; qs('#editAbout').value = user.about||''; };
      const close = () => modal.classList.add('hidden');
      qs('#editProfileBtn').onclick = open;
      qs('#closeEditModal').onclick = close;
      qs('#form-edit').onsubmit = (e) => {
        e.preventDefault();
        const users = storage.getUsers();
        const email = user.email;
        users[email] = { ...users[email], name: qs('#editName').value.trim(), about: qs('#editAbout').value.trim() };
        storage.setUsers(users);
        toast('Profil güncellendi.','success');
        close();
        renderProfile();
      };
    }

    // --- App Init ---
    document.addEventListener('DOMContentLoaded', () => {
      bindAuthUI();

      // If remembered and no explicit route, go directly to profile
      if(!location.hash || location.hash === '#' || location.hash === '#/' || location.hash === '#/home'){
        if(auth.current() && auth.isRemembered()){
          window.location.href = 'templates/index.html';
        } else {
          location.hash = '#/home';
        }
      }

      window.addEventListener('hashchange', navigate);
      navigate();
    });