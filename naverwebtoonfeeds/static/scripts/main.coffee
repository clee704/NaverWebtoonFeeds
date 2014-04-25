$ ->

  # Used to detect changes of search terms in the search bar
  # to make the search almost instant.
  # input event is the right option, but
  # IE 9 doesn't fire input event when the value is changed to blank.
  # So keyup event is used for IE browsers, although
  # it isn't tested whether input works in IE 10.
  searchBarEventType = if /MSIE/.test(navigator.userAgent) then 'keyup' \
                                                           else 'input'

  # Frequently-used jQuery collections
  $body = $('body')
  $form = $('form')
  $searchBar = $form.find('input[type=search]')
  $checkbox = $form.find('input[type=checkbox]')
  $tabs = $('.nav li')
  $seriesList = $('.series-list')
  $seriesElements = $seriesList.find('.series')

  # Use Lazy Load.
  $('img.lazy').lazyload
    effect: 'fadeIn'
    threshold: 1000

  # Select the whole feed URL when it is clicked.
  $seriesList.on 'click', '.series-feed-url input', -> this.select()

  # Prevent submitting the form.
  $form.on 'submit', ->
    $searchBar.blur().triggerHandler(searchBarEventType)
    false
  # Empty the search bar and focus it when X is clicked.
  .find('.close').on 'click', ->
    $searchBar.val('')
    $searchBar.focus().triggerHandler(searchBarEventType)
    false

  # Normalize strings so that they can be searched
  # while hangul syllables are being composed.
  normalize = do ->
    JAMO_LIST = [
      ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ',
       'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ'],
      ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ',
       'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ'],
      ['', 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ',
       'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ',
       'ㅍ', 'ㅎ']
    ]
    DOUBLES =
      'ㄲ': 'ㄱㄱ', 'ㄸ': 'ㄷㄷ', 'ㅃ': 'ㅂㅂ', 'ㅆ': 'ㅅㅅ', 'ㅉ': 'ㅈㅈ', 'ㅘ': 'ㅗㅏ',
      'ㅙ': 'ㅗㅐ', 'ㅚ': 'ㅗㅣ', 'ㅝ': 'ㅜㅓ', 'ㅞ': 'ㅜㅔ', 'ㅟ': 'ㅜㅣ', 'ㅢ': 'ㅡㅣ',
      'ㄳ': 'ㄱㅅ', 'ㄵ': 'ㄴㅈ', 'ㄶ': 'ㄴㅎ', 'ㄺ': 'ㄹㄱ', 'ㄻ': 'ㄹㅁ', 'ㄼ': 'ㄹㅂ',
      'ㄽ': 'ㄹㅅ', 'ㄾ': 'ㄹㅌ', 'ㄿ': 'ㄹㅍ', 'ㅀ': 'ㄹㅎ', 'ㅄ': 'ㅂㅅ'
    decomposeJamo = (jamo) -> if DOUBLES[jamo]? then DOUBLES[jamo] else jamo
    decompose = (str) ->
      temp = []
      for i in [0...str.length]
        c = str.charAt(i)
        if DOUBLES[c]?
          temp.push(DOUBLES[c])
        else if c < '가' || c > '힣'
          temp.push(c)
        else
          x = c.charCodeAt(0) - 0xac00
          jamoCodes = [Math.floor(x / 28 / 21),
                       Math.floor(x / 28) % 21, x % 28]
          temp.push(decomposeJamo(JAMO_LIST[j][jamoCodes[j]])) for j in [0..2]
      temp.join('')
    (str) -> decompose(str.trim().toLowerCase())

  # Index the normalized strings with their IDs.
  tuples = {}
  $seriesElements.each ->
    attrs = ['title', 'author', 'description']
    $this = $(this)
    tuple = (normalize($this.find(".series-#{attr}").text()) for attr in attrs)
    tuples[$this.attr('id')] = tuple

  toggleCompleted = ->
    $body.removeClass('show-ended hide-ended')
    if $checkbox.is(':checked')
      $body.addClass('show-ended')
    else
      $body.addClass('hide-ended')
    organizeTabs()
    updateAlternatingClass()
    loadLazyImagesInCurrentViewport()

  toggleMatched = ->
    $body.removeClass('show-all show-matched')
    $seriesElements.removeClass('matched')
    key = normalize($searchBar.val())
    if key.length == 0
      $body.addClass('show-all')
    else
      $body.addClass('show-matched')
      $seriesElements.each ->
        $this = $(this)
        $this.removeClass('matched unmatched')
        tuple = tuples[$this.attr('id')]
        if (tuple[i].indexOf(key) >= 0 for i in [0..2]).some((x) -> x)
          $this.addClass('matched')
        else
          $this.addClass('unmatched')
    organizeTabs()
    updateAlternatingClass()
    loadLazyImagesInCurrentViewport()

  $tabs.each ->
    $(this).data('day', $(this).find('a').attr('href')[1..])

  DAYS = 'all mon tue wed thu fri sat sun ended'.split(' ')
  DAY_CLASSES = ("show-day-#{day}" for day in DAYS).join(' ')
  toggleSelectedUploadDay = ->
    $tab = location.hash and $("a[href='#{location.hash}']").parent() or
           $tabs.eq(0)
    $body.removeClass(DAY_CLASSES)
    $body.addClass("show-day-#{$tab.data('day')}")
    $tabs.removeClass('active')
    $tab.addClass('active')
    updateAlternatingClass()
    loadLazyImagesInCurrentViewport()

  # Compute the number of visible series elements and hide empty tabs.
  organizeTabs = ->
    $tabs.removeClass('empty')
    $seriesList.removeClass('empty')
    $tabs.each ->
      $this = $(this)
      day = $this.data('day')
      $e = $seriesElements
      $e = $e.filter(".#{day}") if day != 'all'
      $e = $e.filter('.matched') if $body.hasClass('show-matched')
      $e = $e.filter(':not(.ended)') if $body.hasClass('hide-ended')
      if $e.length == 0
        $this.addClass('empty')
    # Select the first tab if the current tab become empty.
    if $tabs.slice(1).is('.active.empty')
      location.href = $tabs.first().find('a').attr('href')
    # Mark the tab content as empty if the first tab is empty.
    if $tabs.first().is('.empty')
      $seriesList.addClass('empty')

  # Update even/odd class for visible series elements
  updateAlternatingClass = ->
    $seriesElements.removeClass('even odd')
    $seriesElements.filter(':visible').each (i) ->
      $(this).addClass(if i % 2 then 'odd' else 'even')

  # Load lazy images currently visible in the viewport.
  loadLazyImagesInCurrentViewport = ->
    $body.trigger('scroll')

  $checkbox.on('click', toggleCompleted).triggerHandler('click')
  $searchBar.on(searchBarEventType, _.debounce(toggleMatched, 200))
  $searchBar.triggerHandler(searchBarEventType)
  $(window).on('hashchange', toggleSelectedUploadDay)
           .triggerHandler('hashchange')
