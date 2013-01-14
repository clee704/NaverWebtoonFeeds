(($) ->

  # Delay the execution of the event handler and only execute
  # the last delayed instance (mostly).
  $.fn.delayedLast = (eventType, options, handler) ->
    settings = $.extend
      delay: 100
    , options
    this.each () ->
      timerId = null
      $(this).on eventType, () ->
        clearTimeout(timerId) if timerId?
        timerId = thisTimerId = setTimeout () ->
          if timerId == thisTimerId
            handler()
        , settings.delay

)(jQuery)
