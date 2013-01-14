$ ->

  # Used to load lazy images when they become visible not by user's scrolling.
  $body = $('body')
  triggerLazyLoad = ->
    setTimeout ->
      # The line below should be run asynchronously or images don't get loaded
      # after clicking a tab.
      $body.trigger('scroll')
    , 0

  # If the current tab is empty, select the first tab (#all).
  $navTabsLi = $('.nav-tabs li')
  selectFirstTabIfCurrentTabIsInvisible = ->
    if not $navTabsLi.slice(1).filter('.active').is(':visible')
      $navTabsLi.first().find('a').tab('show')

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

  # Select the feed URL when clicked.
  $('.tab-pane').on 'click', '.feed-url', (e) -> this.select()

  # Store normalized text for search.
  # Copy media elements to corresponding day tabs.
  $completed = $('#completed')
  $('#all .media').each ->
    $this = $(this)
    uploadDays = $this.data('upload_days').split(',')
    isCompleted = $this.data('is_completed')
    keys = ['title', 'author', 'description']
    $this.data(key, normalize($this.find(".#{key}").text())) for key in keys
    if isCompleted
      $completed.append($this.clone(true))
    else
      for uploadDay in uploadDays
        $("##{uploadDay}").append($this.clone(true))

  # Filter media elements by the query string.
  $tabContent = $('.tab-content')
  $tabContentTabPane = $tabContent.find('.tab-pane')
  $searchQuery = $('.search-query')
  $searchQuery.on 'keyup', (e) ->
    query = normalize($searchQuery.val())
    # Mark all tabs as not empty.
    $navTabsLi.removeClass('empty')
    $tabContentTabPane.removeClass('empty')
    if query.length == 0
      # Quit the filtered state.
      $tabContent.removeClass('filtered')
      triggerLazyLoad()
      return
    # Enter the filtered state.
    $tabContent.addClass('filtered')
    # Mark media as matched if it matches the query string.
    $tabContent.find('.media').each ->
      $this = $(this)
      data = $this.data()
      $this.removeClass('matched')
      if data.title.indexOf(query) >= 0 ||
          data.author.indexOf(query) >= 0 ||
          data.description.indexOf(query) >= 0
        $this.addClass('matched')
    # Hide empty tabs.
    $tabContentTabPane.each (i) ->
      $this = $(this)
      if $this.find('.media.matched').length == 0
        $navTabsLi.eq(i).addClass('empty')
        $this.addClass('empty')
    selectFirstTabIfCurrentTabIsInvisible()
    triggerLazyLoad()
  # Reflect the current status of the search bar.
  .trigger('keyup')

  # Prevent submitting the form.
  $('form').on 'submit', (e) ->
    $searchQuery.trigger('keyup').blur()
    false
  # Empty the search bar and focus it when the close button is clicked.
  .find('.close').on 'click', (e) ->
    $searchQuery.val('').trigger('keyup').focus()
    false

  # Show or hide completed series.
  $showCompleted = $('#show-completed')
  $showCompleted.on 'click custom', (e) ->
    if $showCompleted.is(':checked')
      $body.addClass('show-completed')
    else
      $body.removeClass('show-completed')
      selectFirstTabIfCurrentTabIsInvisible()
    triggerLazyLoad()
  # Reflect the current status of the checkbox.
  .trigger('custom')

  # Use Lazy Load
  $('img.lazy').lazyload
    effect: 'fadeIn'
    threshold: 200
  $navTabsLi.find('a').on('click', triggerLazyLoad)
  $showCompleted.on('click', triggerLazyLoad)
