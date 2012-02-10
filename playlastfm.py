from gi.repository import GObject, RB, Peas
from gi.repository import Gtk
from gi.repository import GLib
import lastfm as lfm
import unicodedata

class PlayLastFmPlugin(GObject.Object, Peas.Activatable):

    _gtype_name__ = 'PlayLastFmPlugin'
    object = GObject.property(type=GObject.Object)

    def __init__(self):
        super(PlayLastFmPlugin, self).__init__()
 
    def do_activate(self):
        print "activating PlayLast.fm plugin"
        self.shell = self.object
        self.db = self.shell.get_property("db")
        self.qm = RB.RhythmDBQueryModel.new_empty(self.db)
        self.entry_type = RB.RhythmDBEntryType()

        ## Create source
        playlist_group = RB.DisplayPageGroup.get_by_id("playlists")
        self.plfm_source = GObject.new( \
                      PlayLastfmSource,
                      entry_type = self.entry_type,
                      shell=self.shell,
                      pixbuf=None,
                      plugin=self)
        self.shell.register_entry_type_for_source(self.plfm_source , self.entry_type)
        self.shell.append_display_page(self.plfm_source, playlist_group)

        ## The following code sets the correct size for your source icon,
        ## finds it by its filename and adds it to a pixbuf.
## FIXME: restore icon support
##        what, width, height = Gtk.icon_size_lookup(Gtk.IconSize.LARGE_TOOLBAR)
##        theme = Gtk.IconTheme.get_default()
##        rb.append_plugin_source_path(theme, "/icons/")
##        icon = rb.try_load_icon(theme, "lastfm", width, 0)
##        # The following code sets the sources "icon" property to the image stored in the pixbuf created above.
##        self.plfm_source.set_property( "pixbuf",  icon) 

        print 'test'
        self.plfm_source.initialise()
        #self.ev = self.plfm_source.entry_view
        self.db_connect_signal()

        self.plfm_source.button.connect("clicked", self.populate)

    def do_deactivate(self):
        print "deactivating sample python plugin"
        self.plfm_source.delete_thyself()
        del self.plfm_source


    def db_connect_signal(self):
        self.db.connect('load-complete', self.db_load_complete)

    def db_load_complete(self, db):
        self.load_complete = True
        self.populate()

    def populate(self, widget=None):

        # Get parameters
        user = self.plfm_source.username_entry.get_property("text")
        if len(user) < 0:
            return
        week_nb_str = self.plfm_source.time_entry.get_property("text")
        try:
            week_nb = int(week_nb_str)
        except:
            return

        # Retrieve chart list from Last.fm
        print "fetching songs for %s, for the last %d weeks" % (user, week_nb)
        my_lfm   = lfm.lastfm_handle()
        my_lfm.set_user(user)
        songs = my_lfm.get_chart_songs(week_nb)
        print "Last.fm song count: %d" % len(songs)

        # Retrieve songs from DB
        print "Trying to query the RhythmDB for the song list."
        self.qm = RB.RhythmDBQueryModel.new_empty(self.db)
        song_len = len(songs)
        for i in range(song_len):
            qm_tmp = RB.RhythmDBQueryModel.new_empty(self.db)
            query = GLib.PtrArray()
            my_song = songs[i]
            print "Querying for %s" % my_song
            artist = unicodedata.normalize('NFKD', 
                my_song['artist'].lower()).encode('ascii', 'ignore')
            title  = unicodedata.normalize('NFKD',
                my_song['name'].lower()).encode('ascii', 'ignore')
            self.db.query_append_params(query,
                RB.RhythmDBQueryType.FUZZY_MATCH, 
                RB.RhythmDBPropType.ARTIST_FOLDED, artist )
            self.db.query_append_params(query, 
                RB.RhythmDBQueryType.FUZZY_MATCH, 
                RB.RhythmDBPropType.TITLE_FOLDED, title )
            #if i < song_len-1:
                #self.db.query_append_params( query, 
                    #RB.RhythmDBQueryType.DISJUNCTIVE_MARKER, 
                    #RB.RhythmDBPropType.TYPE, '' )
            # Perform query
            self.db.do_full_query_parsed(qm_tmp, query)
            if len(qm_tmp) > 0:
                # only add the first match
                #FIXME: implement better duplicate management
                self.qm.add_entry(qm_tmp[0][0], -1)

        # Update view
        self.plfm_source.props.query_model = self.qm
        self.plfm_source.get_entry_view().set_model(self.qm)


class PlayLastfmSource(RB.BrowserSource):

    def __init__(self):
        RB.BrowserSource.__init__(self, name=_("PlayLast.fm"))

    def initialise(self):
        top_grid = self.get_children()[0]

        shell = self.props.shell

        vbox = Gtk.VBox()
        vbox.set_homogeneous(False)

        # Header
        hbox = Gtk.HBox()
        label = Gtk.Label()
        label.set_use_markup(True)
        label.set_markup("<span size='large' weight='bold'>Create a playlist with the following criterions:</span>")
        hbox.pack_start(label, False, False, 0)
        vbox.pack_start(hbox, False, False, 5)

        # Fields
        hbox = Gtk.HBox()
        label = Gtk.Label("The user is ")
        self.username_entry = Gtk.Entry()
        self.username_entry.set_property("width-chars",15)
        hbox.pack_start(label, False, False, 5)
        hbox.pack_start(self.username_entry, False, False, 0)
        vbox.pack_start(hbox, False, False, 5)

        hbox = Gtk.HBox()
        label = Gtk.Label("The songs have been listened during the last")
        hbox.pack_start(label, False, False, 5)
        self.time_entry = Gtk.Entry()
        self.time_entry.set_max_length(2)
        self.time_entry.set_property("width-chars",4)
        hbox.pack_start(self.time_entry, False, False, 0)
        label = Gtk.Label(" weeks.")
        hbox.pack_start(label, False, False, 5)
        vbox.pack_start(hbox, False, False, 5)

        hbox = Gtk.HBox()
        self.button = Gtk.Button()
        self.button.set_property("label", "Create playlist")
        hbox.pack_end(self.button, False, False, 0)
        vbox.pack_start(hbox, False, False, 5)

        ## Entry view
        #self.entry_view = RB.EntryView(None, None) # shell.props.db,  shell.get_player()) #, "", True, False)
        #self.entry_view.append_column(RB.EntryViewColumn.TITLE, True)
        #self.entry_view.append_column(RB.EntryViewColumn.ARTIST, True)
        #self.entry_view.append_column(RB.EntryViewColumn.DURATION, True)
        #self.entry_view.set_sorting_order("Artist", Gtk.SortType.ASCENDING)
##FIXME        self.entry_view.set_policy(Gtk.POLICY_AUTOMATIC, Gtk.POLICY_AUTOMATIC)
##FIXME        self.entry_view.set_shadow_type(Gtk.SHADOW_IN)

        vbox.pack_start(hbox, False, False, 0)
        top_grid.insert_row(0)
        top_grid.attach(vbox, 0,0,1,1)
        self.show_all()

#    def do_impl_activate (self):
#        if not self.activated:
#            self.activated = True
#        rb.BrowserSource.do_impl_activate (self)

GObject.type_register(PlayLastfmSource)
