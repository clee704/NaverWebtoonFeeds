$ ->

  # jQuery collections that are used often.
  $body = $('body')
  $form = $('form')
  $searchBar = $form.find('input[type=search]')
  $checkbox = $form.find('input[type=checkbox]')
  $tabs = $('.nav-tabs li')
  $tabContent = $('.tab-content')
  $mediaElements = $tabContent.find('.media')

  # Use Lazy Load.
  $('img.lazy').lazyload
    effect: 'fadeIn'
    threshold: 200

  # Select the whole feed URL when it is clicked.
  $tabContent.on 'click', '.feed-url', -> this.select()

  # Prevent submitting the form.
  $form.on 'submit', ->
    $searchBar.triggerHandler('input').blur()
    false
  # Empty the search bar and focus it when the close button is clicked.
  .find('.close').on 'click', ->
    $searchBar.val('').triggerHandler('input').focus()
    false

  # Normalize the string for search.
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
          jamoCodes = [Math.floor(x / 28 / 21), Math.floor(x / 28) % 21, x % 28]
          temp.push(decomposeJamo(JAMO_LIST[j][jamoCodes[j]])) for j in [0..2]
      temp.join('')
    (str) -> decompose(str.trim().toLowerCase())

  # Store normalized text for search.
  tuples = {}
  $mediaElements.each ->
    attrs = ['title', 'author', 'description']
    $this = $(this)
    tuple = (normalize($this.find(".#{attr}").text()) for attr in attrs)
    tuples[$this.attr('id')] = tuple

  toggleCompletedSeries = ->
    $body.removeClass('show-completed hide-completed')
    if $checkbox.is(':checked')
      $body.addClass('show-completed')
    else
      $body.addClass('hide-completed')
    organizeTabs()
    loadLazyImagesInCurrentViewport()

  toggleMatchedSeries = ->
    $body.removeClass('show-all show-matched')
    $mediaElements.removeClass('matched')
    key = normalize($searchBar.val())
    if key.length == 0
      $body.addClass('show-all')
    else
      $body.addClass('show-matched')
      $mediaElements.each ->
        $this = $(this)
        $this.removeClass('matched unmatched')
        tuple = tuples[$this.attr('id')]
        if (tuple[i].indexOf(key) >= 0 for i in [0..2]).some((x) -> x)
          $this.addClass('matched')
        else
          $this.addClass('unmatched')
    organizeTabs()
    loadLazyImagesInCurrentViewport()

  $tabs.each ->
    $(this).data('day', $(this).find('a').attr('href')[1..])

  DAYS = 'all mon tue wed thu fri sat sun completed'.split(' ')
  DAY_CLASSES = ("show-day-#{day}" for day in DAYS).join(' ')
  toggleSelectedUploadDaySeries = ->
    $tab = $(this).parent()
    $body.removeClass(DAY_CLASSES)
    $body.addClass("show-day-#{$tab.data('day')}")
    $tabs.removeClass('active')
    $tab.addClass('active')
    loadLazyImagesInCurrentViewport()
    # Prevent the hash from appearing at the address bar.
    false

  organizeTabs = ->
    # Compute the number of visible media elements and hide empty tabs.
    $tabs.removeClass('empty')
    $tabContent.removeClass('empty')
    $tabs.each ->
      $this = $(this)
      day = $this.data('day')
      $e = $mediaElements
      $e = $e.filter(".#{day}") if day != 'all'
      $e = $e.filter('.matched') if $body.hasClass('show-matched')
      $e = $e.filter(':not(.completed)') if $body.hasClass('hide-completed')
      if $e.length == 0
        $this.addClass('empty')
    # Select the first tab if the current tab become empty.
    if $tabs.slice(1).is('.active.empty')
      $tabs.first().find('a').triggerHandler('click')
    # Mark the tab content as empty if the first tab is empty.
    if $tabs.first().is('.empty')
      $tabContent.addClass('empty')

  loadLazyImagesInCurrentViewport = ->
    # Load lazy images currently visible in the viewport.
    $body.trigger('scroll')

  $checkbox.on('click', toggleCompletedSeries).triggerHandler('click')
  $searchBar.on('input', toggleMatchedSeries).triggerHandler('input')
  $tabs.find('a').on('click', toggleSelectedUploadDaySeries)
  $tabs.filter('.active').find('a').triggerHandler('click')
