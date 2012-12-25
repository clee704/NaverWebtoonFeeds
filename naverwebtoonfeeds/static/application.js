$(function () {

  // Normalize the string for search.
  function normalize(str) {
    return decompose(str.trim().toLowerCase());
  }

  initials = [
    'ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ',
    'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'
  ];
  medials = [
    'ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ',
    'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ'
  ];
  finals = [
    '', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ',
    'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ',
    'ㅌ', 'ㅍ', 'ㅎ'
  ];
  doubles = {
    'ㄲ': 'ㄱㄱ', 'ㄸ': 'ㄷㄷ', 'ㅃ': 'ㅂㅂ', 'ㅆ': 'ㅅㅅ', 'ㅉ': 'ㅈㅈ',
    'ㅘ': 'ㅗㅏ', 'ㅙ': 'ㅗㅐ', 'ㅚ': 'ㅗㅣ', 'ㅝ': 'ㅜㅓ', 'ㅞ': 'ㅜㅔ',
    'ㅟ': 'ㅜㅣ', 'ㅢ': 'ㅡㅣ', 'ㄳ': 'ㄱㅅ', 'ㄵ': 'ㄴㅈ', 'ㄶ': 'ㄴㅎ',
    'ㄺ': 'ㄹㄱ', 'ㄻ': 'ㄹㅁ', 'ㄼ': 'ㄹㅂ', 'ㄽ': 'ㄹㅅ', 'ㄾ': 'ㄹㅌ',
    'ㄿ': 'ㄹㅍ', 'ㅀ': 'ㄹㅎ', 'ㅄ': 'ㅂㅅ'
  };
  function decompose(str) {
    var temp = [];
    for (var i = 0; i < str.length; i++) {
      var c = str.charAt(i);
      if (c in doubles) {
        temp.push(doubles[c]);
      }
      else if (c < '가' || c > '힣') {
        temp.push(c);
      }
      else {
        var v = c.charCodeAt(0) - 0xac00,
            initialCode = Math.floor(v / 28 / 21),
            medialCode = Math.floor(v / 28) % 21,
            finalCode = v % 28,
            initial = initials[initialCode],
            medial = medials[medialCode],
            final = finals[finalCode];
        temp.push(initial in doubles ? doubles[initial] : initial);
        temp.push(medial in doubles ? doubles[medial] : medial);
        temp.push(final in doubles ? doubles[final] : final);
      }
    }
    return temp.join('');
  }
  window.decompose = decompose;

  // Select the feed URL when clicked.
  $('.tab-pane').on('click', '.feed-url', function (e) {
    this.select();
  });

  // Store normalized text for search.
  // Add copied media elements to day tabs.
  $('.media').each(function () {
    var $this = $(this),
        updateDays = $this.data('update_days').split(',');
    $this.data('title', normalize($this.find('.title').text()));
    $this.data('author', normalize($this.find('.author').text()));
    $this.data('description', normalize($this.find('.description').text()));
    for (var i = 0; i < updateDays.length; i++) {
      $('#' + updateDays[i]).append($this.clone(true));
    }
  });

  // Filter media elements by the query string.
  $navTabsLi = $('.nav-tabs li');
  $tabContent = $('.tab-content');
  $tabContentTabPane = $tabContent.find('.tab-pane');
  $searchQuery = $('.search-query');
  $searchQuery.on('keyup', function (e) {
    var query = normalize($(this).val());
    $navTabsLi.removeClass('empty');
    $tabContentTabPane.removeClass('empty');
    if (query.length == 0) {
      $tabContent.removeClass('filtered');
      return;
    }
    $tabContent.addClass('filtered');
    $tabContent.find('.media').each(function () {
      var $this = $(this),
          data = $this.data();
      $this.removeClass('show');
      if (data.title.indexOf(query) >= 0 ||
          data.author.indexOf(query) >= 0 ||
          data.description.indexOf(query) >= 0) {
        $this.addClass('show');
      }
    });
    $tabContentTabPane.each(function (i) {
      var $this = $(this);
      if ($this.find('.media.show').length == 0) {
        $navTabsLi.eq(i).addClass('empty');
        $this.addClass('empty');
      }
    });
    if ($navTabsLi.slice(1).is('.active.empty')) {
      $navTabsLi.first().find('a').tab('show');
    }
  }).trigger('keyup');
  $('.form-search').on('submit', function (e) {
    $searchQuery.trigger('keyup').blur();
    return false;
  }).find('.close').on('click', function (e) {
    $searchQuery.val('').trigger('keyup').focus();
    return false;
  });
});
