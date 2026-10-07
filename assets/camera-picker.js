/* 카메라 선택·변경 (16·17·23강 공용)
 * - 페이지의 getUserMedia 호출을 감싸서, 기억해 둔 카메라(localStorage 'ebs.cameraId')로 시작한다.
 * - 카메라가 켜지면 화면 아래에 "📷 카메라" 선택 상자를 띄우고, 바꾸면 같은 MediaStream 안의 영상 트랙만 갈아 끼운다.
 *   (페이지가 쥐고 있는 stream 변수·끄기 코드는 그대로 동작)
 */
(function () {
  var md = navigator.mediaDevices;
  if (!md || !md.getUserMedia) return;
  var KEY = 'ebs.cameraId';
  var orig = md.getUserMedia.bind(md);
  var streams = [];          // 이 스크립트가 넘겨준 영상 스트림들
  var box = null, sel = null;

  function saved() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function save(id) { try { localStorage.setItem(KEY, id); } catch (e) { } }

  function withDevice(c, id) {
    var v = (c.video && typeof c.video === 'object') ? Object.assign({}, c.video) : {};
    delete v.facingMode;
    v.deviceId = { exact: id };
    return Object.assign({}, c, { video: v });
  }

  function liveTrack() {
    for (var i = streams.length - 1; i >= 0; i--) {
      var t = streams[i].getVideoTracks().filter(function (t) { return t.readyState === 'live'; })[0];
      if (t) return { stream: streams[i], track: t };
    }
    return null;
  }

  md.getUserMedia = function (c) {
    if (!c || !c.video) return orig(c);
    var id = saved();
    var p = id ? orig(withDevice(c, id)).catch(function () { return orig(c); }) : orig(c);
    return p.then(function (s) { streams.push(s); setTimeout(refresh, 0); return s; });
  };

  function ensureUi() {
    if (box) return;
    box = document.createElement('div');
    box.id = 'ebsCamPicker';
    box.setAttribute('role', 'group');
    box.setAttribute('aria-label', '카메라 고르기');
    box.style.cssText = 'position:fixed;left:50%;bottom:16px;transform:translateX(-50%);z-index:9999;display:none;' +
      'align-items:center;gap:8px;background:#FBF7EC;color:#141414;border:3px solid #141414;border-radius:14px;' +
      'box-shadow:4px 4px 0 #141414;padding:8px 12px;font:800 14px/1.2 -apple-system,"Segoe UI","Malgun Gothic",sans-serif;max-width:calc(100vw - 32px)';
    var label = document.createElement('label');
    label.textContent = '📷 카메라';
    label.htmlFor = 'ebsCamSelect';
    sel = document.createElement('select');
    sel.id = 'ebsCamSelect';
    sel.style.cssText = 'font:700 14px inherit;border:2px solid #141414;border-radius:9px;padding:5px 8px;background:#fff;color:#141414;max-width:60vw';
    sel.addEventListener('change', function () { switchTo(sel.value); });
    box.appendChild(label);
    box.appendChild(sel);
    document.body.appendChild(box);
  }

  function refresh() {
    var cur = liveTrack();
    if (!cur) { if (box) box.style.display = 'none'; return; }
    ensureUi();
    md.enumerateDevices().then(function (list) {
      var cams = list.filter(function (d) { return d.kind === 'videoinput'; });
      var curId = cur.track.getSettings().deviceId;
      sel.innerHTML = '';
      cams.forEach(function (d, i) {
        var o = document.createElement('option');
        o.value = d.deviceId;
        o.textContent = d.label || ('카메라 ' + (i + 1));
        if (d.deviceId === curId) o.selected = true;
        sel.appendChild(o);
      });
      sel.disabled = cams.length < 2;
      box.title = cams.length < 2 ? '연결된 카메라가 1개예요' : '다른 카메라로 바꿀 수 있어요';
      box.style.display = 'flex';
    });
  }

  // 강별 [끄기, 켜기] 버튼: 카메라를 바꾸면 페이지의 원래 절차로 껐다 켠다.
  // (영상 트랙만 바꾸면 그 사이 빈 프레임 때문에 MediaPipe 그래프가 망가진다)
  var RESTART = { '16': ['#btnStart', '#btnStart'], '17': ['#camOff', '#camOn'], '23': ['#btnStart', '#btnStart'] };
  var lesson = (location.pathname.match(/\/(\d+)\/?$/) || [])[1];

  function switchTo(id) {
    var cur = liveTrack();
    if (!cur) return;
    var r = RESTART[lesson];
    if (r) {
      // 고른 카메라를 기억하고 페이지를 새로 열어 깨끗한 상태로 다시 켠다
      save(id);
      sel.disabled = true;
      try { sessionStorage.setItem('ebs.camAutostart', lesson); } catch (e) { }
      cur.stream.getTracks().forEach(function (t) { t.stop(); });
      location.reload();
      return;
    }
    var s = cur.stream, old = cur.track;
    var settings = old.getSettings();
    var c = { video: { deviceId: { exact: id } }, audio: false };
    if (settings.width) c.video.width = { ideal: settings.width };
    if (settings.height) c.video.height = { ideal: settings.height };
    sel.disabled = true;
    old.stop();   // 같은 카메라를 두 번 열 수 없는 기기 대비: 먼저 놓아 준다
    orig(c).then(function (ns) {
      var nt = ns.getVideoTracks()[0];
      s.removeTrack(old);
      s.addTrack(nt);
      save(id);
      document.querySelectorAll('video').forEach(function (v) {
        if (v.srcObject === s) { v.srcObject = null; v.srcObject = s; var pr = v.play(); if (pr && pr.catch) pr.catch(function () { }); }
      });
    }).catch(function () {
      alert('그 카메라를 켤 수 없어요. 다른 프로그램이 쓰고 있는지 확인해 주세요.');
    }).then(function () { sel.disabled = false; refresh(); });
  }

  // 페이지의 끄기 버튼(track.stop)은 이벤트가 없으므로 주기적으로 상태를 맞춘다
  setInterval(function () {
    var on = !!liveTrack();
    if (box && (box.style.display !== 'none') !== on) { if (on) refresh(); else box.style.display = 'none'; }
  }, 700);
  if (md.addEventListener) md.addEventListener('devicechange', refresh);

  // 카메라를 바꾸느라 새로 연 페이지면 자동으로 다시 켜기
  var auto = null;
  try { auto = sessionStorage.getItem('ebs.camAutostart'); sessionStorage.removeItem('ebs.camAutostart'); } catch (e) { }
  if (auto && auto === lesson && RESTART[lesson]) {
    window.addEventListener('load', function () {
      setTimeout(function () { var b = document.querySelector(RESTART[lesson][1]); if (b) b.click(); }, 400);
    });
  }

  window.__ebsCam = {
    liveVideoDeviceId: function () { var c = liveTrack(); return c ? c.track.getSettings().deviceId : null; }
  };
})();
