from blinker import Namespace


view_signals = Namespace()

index_requested = view_signals.signal('index-requested')
feed_requested = view_signals.signal('feed-requested')
