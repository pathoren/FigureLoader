import numpy as np
import wx
from wx.py.shell import Shell
import pickle
import re
import os

import matplotlib
matplotlib.use('WxAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wxagg import NavigationToolbar2WxAgg
import matplotlib.pyplot as plt
from matplotlib.widgets import SpanSelector
from matplotlib.patches import Rectangle
import numpy.polynomial.polynomial as poly
# matplotlib.use('Qt4Agg')

import matplotlib.colors as colors
cv = colors.ColorConverter()
white_level = 0.2
w_rgb = cv.to_rgb('w')
b_rgb = cv.to_rgb('b')
r_rgb = cv.to_rgb('r')
y_rgb = cv.to_rgb('y')
g_rgb = cv.to_rgb('g')
m_rgb = cv.to_rgb('m')
c_rgb = cv.to_rgb('c')

# Create color maps
cmaps0 = dict()
cmaps0['b'] = colors.LinearSegmentedColormap.from_list('', [w_rgb, b_rgb])
cmaps0['r'] = colors.LinearSegmentedColormap.from_list('', [w_rgb, r_rgb])
cmaps0['y'] = colors.LinearSegmentedColormap.from_list('', [w_rgb, y_rgb])
cmaps0['g'] = colors.LinearSegmentedColormap.from_list('', [w_rgb, g_rgb])
cmaps0['m'] = colors.LinearSegmentedColormap.from_list('', [w_rgb, m_rgb])
cmaps0['c'] = colors.LinearSegmentedColormap.from_list('', [w_rgb, c_rgb])

# Modifed cmaps
# Colormaps work only with integer input values, for floats cmap endvalues are returned
my_cmaps = dict()
my_cmaps['b'] = colors.LinearSegmentedColormap.from_list('', [cmaps0['b'](int(np.rint(white_level * 255))), b_rgb])
my_cmaps['r'] = colors.LinearSegmentedColormap.from_list('', [cmaps0['r'](int(np.rint(white_level * 255))), r_rgb])
my_cmaps['y'] = colors.LinearSegmentedColormap.from_list('', [cmaps0['y'](int(np.rint(white_level * 255))), y_rgb])
my_cmaps['g'] = colors.LinearSegmentedColormap.from_list('', [cmaps0['g'](int(np.rint(white_level * 255))), g_rgb])
my_cmaps['m'] = colors.LinearSegmentedColormap.from_list('', [cmaps0['m'](int(np.rint(white_level * 255))), m_rgb])
my_cmaps['c'] = colors.LinearSegmentedColormap.from_list('', [cmaps0['c'](int(np.rint(white_level * 255))), c_rgb])




class MyDialog(wx.Dialog):
    def __init__(self, parent, id, title):
        wx.Dialog.__init__(self, parent, id, title)


class Toolbar(NavigationToolbar2WxAgg):
    _LINESELECT = wx.NewId()
    _PIXELINSPECTOR = wx.NewId()

    toolitems = (
        # ('Home', 'Reset original view', 'home', 'home'),
        # ('Back', 'Back to  previous view', 'back', 'back'),
        # ('Forward', 'Forward to next view', 'forward', 'forward'),
        # (None, None, None, None),
        (None, None, None, None),
        ('Pan', 'Pan axes with left mouse, zoom with right', 'move', 'pan'),
        ('Zoom', 'Zoom to rectangle', 'zoom_to_rect', 'zoom'),
        (None, None, None, None),
        ('Subplots', 'Configure subplots', 'subplots', 'configure_subplots'),
        ('Save', 'Save the figure', 'filesave', 'save_figure'),
      )

    def __init__(self,  canvas):
        NavigationToolbar2WxAgg.__init__(self,canvas)

        # # In mpl 1.2 the Toolbar is restructured which requires a hack
        # if int(matplotlib.__version__.split('.')[1]) >= 2:
        #     self._NTB2_PAN = self.wx_ids['Pan']
        #     self._NTB2_ZOOM = self.wx_ids['Zoom']

        # self._CHECK_TOOLS = (self._NTB2_PAN,self._NTB2_ZOOM,self._LINESELECT,self._PIXELINSPECTOR)
        self.canvas = canvas

    # def save_figure(self, *args):
    #     # Fetch the required filename and file type.
    #     filetypes, exts, filter_index = self.canvas._get_imagesave_wildcards()
    #     default_file = self.canvas.get_default_filename()
    #     dlg = wx.FileDialog(self._parent, "Save to file", "", default_file,
    #                         filetypes,
    #                         wx.SAVE|wx.OVERWRITE_PROMPT)
    #     dlg.SetFilterIndex(filter_index)
    #     if dlg.ShowModal() == wx.ID_OK:
    #         dirname  = dlg.GetDirectory()
    #         filename = dlg.GetFilename()
    #         DEBUG_MSG('Save file dir:%s name:%s' % (dirname, filename), 3, self)
    #         format = exts[dlg.GetFilterIndex()]
    #         basename, ext = os.path.splitext(filename)
    #         if ext.startswith('.'):
    #             ext = ext[1:]
    #         if ext in ('svg', 'pdf', 'ps', 'eps', 'png') and format!=ext:
    #             #looks like they forgot to set the image type drop
    #             #down, going with the extension.
    #             warnings.warn('extension %s did not match the selected image type %s; going with %s'%(ext, format, ext), stacklevel=0)
    #             format = ext
    #         try:
    #             self.canvas.print_figure(
    #                 os.path.join(dirname, filename), format=format)
    #         except Exception as e:
    #             error_msg_wx(str(e))

    def set_history_buttons(self):
        """Enable or disable back/forward button"""
        pass

    def any_tool_active(self):
        state = [tb.GetToolState(x) for x in tb.wx_ids.values()]
        #if any state is true, one tool is clicked
        if True in state: return True
        else: return False 


# Get a list of the colormaps in matplotlib.  Ignore the ones that end with
# '_r' because these are simply reversed versions of ones that don't end
# with '_r'
valid_cmaps = sorted(m for m in plt.cm.datad if not m.endswith("_r"))
valid_artists = [matplotlib.collections.PathCollection, matplotlib.lines.Line2D, matplotlib.image.AxesImage]
ARTIST_PATH = 0
ARTIST_LINE2D = 1
ARTIST_IMSHOW = 2

class MySpanSelector(SpanSelector):
    def __init__(self, *args, **kwargs):
        SpanSelector.__init__(self, *args, **kwargs)

    def deactivate_hspan(self):
        self.canvas.mpl_disconnect(self.cid_button_press_event)

    def activate_hspan(self, callback):
        cid = self.canvas.mpl_connect('button_preses_event', callback)
        self.cid_button_press_event = cid


class ToolPanel(wx.Panel):

    def __init__(self, parent):
        
        
        ADDICT_TEXT ={'proportion':0, 'flag' :wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL,'border':5 }
        ADDICT_ITEM ={'proportion':0, 'flag' :wx.GROW|wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL,'border':5 }

        self.parent = parent
        wx.Panel.__init__(self, parent)
        gridsizer = wx.FlexGridSizer(cols=2)

        gridsizer.Add(wx.StaticText(self, -1, ' '), **ADDICT_TEXT)
        gridsizer.Add(wx.StaticText(self, -1, ' '), **ADDICT_TEXT)
        gridsizer.Add(wx.StaticText(self, -1, ' FIGURE: '), **ADDICT_TEXT)
        gridsizer.Add(wx.StaticText(self, -1, ' '), **ADDICT_TEXT)

        self.dpi = 1
        (self.screen_x, self.screen_y) = wx.DisplaySizeMM()
        (self.screen_x, self.screen_y) = int(self.screen_x/10./2.54), int(self.screen_y/10./2.54) # scale to inches
        self.spin_x = wx.SpinCtrl(self, -1, size=wx.Size(40, -1), min=1, max=self.screen_x)
        self.spin_y = wx.SpinCtrl(self, -1, size=wx.Size(40, -1), min=1, max=self.screen_y)
        self.Bind(wx.EVT_SPINCTRL, self.OnSizeSpinner, self.spin_x)
        self.Bind(wx.EVT_SPINCTRL, self.OnSizeSpinner, self.spin_y)

        szr = wx.BoxSizer(wx.HORIZONTAL)
        szr.Add(self.spin_x, 1, wx.GROW)
        szr.Add(self.spin_y, 1, wx.GROW)
        gridsizer.Add(wx.StaticText(self, -1, '  Size (x, y) inch: '),  **ADDICT_TEXT)
        gridsizer.Add(szr, **{'proportion':1, 'flag': wx.GROW} )

        gridsizer.Add(wx.StaticText(self, -1, ' '), **ADDICT_TEXT)
        gridsizer.Add(wx.StaticText(self, -1, ' '), **ADDICT_TEXT)
        gridsizer.Add(wx.StaticText(self, -1, ' AXES: '), **ADDICT_TEXT)
        gridsizer.Add(wx.StaticText(self, -1, ' '), **ADDICT_TEXT)
        choices = []
        for i, a in enumerate(parent.canvas.figure.get_axes()):
            choices.append('Axis ({}, {})'.format(i/a.numCols, i%a.numCols))  
        self.cb_axes = wx.ComboBox(self, id=-1, choices=choices)
        self.cb_axes.SetSelection(0)
        self.Bind(wx.EVT_COMBOBOX, self.OnAxes, self.cb_axes)
        gridsizer.Add(wx.StaticText(self, -1, '  Axis: '), **ADDICT_TEXT)
        gridsizer.Add(self.cb_axes, **ADDICT_ITEM)


        self.txt_title = wx.TextCtrl(self, -1, '')
        gridsizer.Add(wx.StaticText(self, -1, '  Title: '),  **ADDICT_TEXT)
        gridsizer.Add(self.txt_title, **ADDICT_ITEM)

        self.txt_xlabel = wx.TextCtrl(self, -1, '')
        gridsizer.Add(wx.StaticText(self, -1, '  xlabel: '),  **ADDICT_TEXT)
        gridsizer.Add(self.txt_xlabel, **ADDICT_ITEM)

        self.cb_xscale = wx.ComboBox(self, -1, choices=['linear', 'log'])
        gridsizer.Add(wx.StaticText(self, -1, '  xscale: '), **ADDICT_TEXT)
        gridsizer.Add(self.cb_xscale, **ADDICT_ITEM)

        self.txt_xticks = wx.TextCtrl(self, -1, '')
        gridsizer.Add(wx.StaticText(self, -1, '  xticks: '),  **ADDICT_TEXT)
        gridsizer.Add(self.txt_xticks, **ADDICT_ITEM)

        self.txt_xlims = wx.TextCtrl(self, -1, '')
        gridsizer.Add(wx.StaticText(self, -1, '  xlims: '), **ADDICT_TEXT)
        gridsizer.Add(self.txt_xlims, **ADDICT_ITEM)


        self.txt_ylabel = wx.TextCtrl(self, -1, '')
        gridsizer.Add(wx.StaticText(self, -1, '  ylabel: '),  **ADDICT_TEXT)
        gridsizer.Add(self.txt_ylabel, **ADDICT_ITEM)

        self.cb_yscale = wx.ComboBox(self, -1, choices=['linear', 'log'])
        gridsizer.Add(wx.StaticText(self, -1, '  yscale: '), **ADDICT_TEXT)
        gridsizer.Add(self.cb_yscale, **ADDICT_ITEM)

        self.txt_yticks = wx.TextCtrl(self, -1, '')
        gridsizer.Add(wx.StaticText(self, -1, '  yticks: '), **ADDICT_TEXT)
        gridsizer.Add(self.txt_yticks, **ADDICT_ITEM)

        self.txt_ylims = wx.TextCtrl(self, -1, '')
        gridsizer.Add(wx.StaticText(self, -1, '  ylims: '), **ADDICT_TEXT)
        gridsizer.Add(self.txt_ylims, **ADDICT_ITEM)
        
        
        gridsizer.Add(wx.StaticText(self, -1, ' '), **ADDICT_TEXT)
        gridsizer.Add(wx.StaticText(self, -1, ' '), **ADDICT_TEXT)
        gridsizer.Add(wx.StaticText(self, -1, ' ARTISTS: '), **ADDICT_TEXT)
        gridsizer.Add(wx.StaticText(self, -1, ' '), **ADDICT_TEXT)



        # Combobox for artists
        choices = []
        for i, art in enumerate(self._GetArtists(parent.canvas.figure.get_axes()[0])[0]):
            choices.append(art.__str__())  
        self.cb_artists = wx.ComboBox(self, id=-1, choices=choices)
        self.cb_artists.SetSelection(0)
        self.Bind(wx.EVT_COMBOBOX, self.OnArtists, self.cb_artists)
        gridsizer.Add(wx.StaticText(self, -1, '  Artist: '), **ADDICT_TEXT)
        gridsizer.Add(self.cb_artists, **ADDICT_ITEM)


        self.txt_color = wx.TextCtrl(self, -1, '')
        gridsizer.Add(wx.StaticText(self, -1, '  Color: '), **ADDICT_TEXT)
        gridsizer.Add(self.txt_color, **ADDICT_ITEM)
        self._SetColorTooltip(artist_id=ARTIST_LINE2D)

        choices = ['-', '--', '-.', ':']
        self.cb_artiststyle = wx.ComboBox(self, id=-1, choices=choices)
        self.cb_artiststyle.SetSelection(0)
        gridsizer.Add(wx.StaticText(self, -1, '  Linestyle: '), **ADDICT_TEXT)
        gridsizer.Add(self.cb_artiststyle, **ADDICT_ITEM)
        
        choices = ['None','*','.',',','^','d','v','>','<']
        self.cb_marker = wx.ComboBox(self, id=-1, choices=choices)
        self.cb_marker.SetSelection(0)
        gridsizer.Add(wx.StaticText(self, -1, '  Marker: '), **ADDICT_TEXT)
        gridsizer.Add(self.cb_marker, **ADDICT_ITEM)

        self.txt_name = wx.TextCtrl(self, -1, '')
        gridsizer.Add(wx.StaticText(self, -1, '  Label: '), **ADDICT_TEXT)
        gridsizer.Add(self.txt_name, **ADDICT_ITEM)

        choices = ['best', 'upper right', 'upper left', 
                   'lower left', 'lower right', 'right', 
                   'center left', 'center right', 
                   'lower center', 'upper center', 'center']
        self.cb_legend_pos = wx.ComboBox(self, id=-1, choices=choices)
        self.cb_legend_pos.SetSelection(0)
        gridsizer.Add(wx.StaticText(self, -1, '  Legend pos: '), **ADDICT_TEXT)
        gridsizer.Add(self.cb_legend_pos, **ADDICT_ITEM)

        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(gridsizer, 0, wx.GROW|wx.ALL, 5)

        self.btn_update = wx.Button(self, -1, 'Update')
        self.sizer.Add(self.btn_update, **ADDICT_ITEM)
        self.Bind(wx.EVT_BUTTON, self.Update, self.btn_update)

        self.btn_tight_layout = wx.Button(self, -1, 'Tight layout')
        self.sizer.Add(self.btn_tight_layout, **ADDICT_ITEM)
        self.Bind(wx.EVT_BUTTON, self.TightLayout, self.btn_tight_layout)

        self.btn_legend = wx.ToggleButton(self, -1, 'Generate legend')
        self.sizer.Add(self.btn_legend, **ADDICT_ITEM)
        self.Bind(wx.EVT_TOGGLEBUTTON, self.GenerateLegend, self.btn_legend)

        # self.btn_fitfunc = wx.ToggleButton(self, -1, 'Fit function')
        # self.sizer.Add(self.btn_fitfunc, **ADDICT_ITEM)
        # self.Bind(wx.EVT_TOGGLEBUTTON, self.fit_func, self.btn_fitfunc) 

        self._SetAxis(parent.canvas.figure.get_axes()[0])
        
        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()




    def UpdateFigureSize(self, fig):
        (x, y) = fig.get_size_inches()
        self.dpi = fig.get_dpi()
        # x_pix, y_pix = x*self.dpi, y*self.dpi
        self.spin_x.SetValue(x)
        self.spin_y.SetValue(y)

    def OnSizeSpinner(self, event):
        x, y = self.spin_x.GetValue()*self.dpi, self.spin_y.GetValue()*self.dpi
        self.parent.canvas.SetMinSize(wx.Size(x, y))
        self.Fit()
        self.parent.Fit()
        self.parent.parent.Fit()

    def _HasLegend(self, ax):
        if type(ax.get_legend()) != type(None):
            return True
        else: return False

    def GenerateLegend(self, event):
        ax = self.parent.canvas.figure.get_axes()[self.cb_axes.GetSelection()]
        if self._HasLegend(ax):
            ax.get_legend().remove()
            self.btn_legend.SetLabel('Generate legend')
            self.btn_legend.SetValue(False)
        else:
            line = ax.get_lines()
            lab = [l.get_label() for l in line]
            loc = self.cb_legend_pos.GetStringSelection()
            ax.legend(line, lab, loc=loc)
            self.btn_legend.SetValue(True)
            self.btn_legend.SetLabel('Remove legend')
        wx.CallAfter(self.parent.canvas.draw)



    def _GetArtists(self, ax):
        
        children = ax.get_children()
        artists = []
        for child in children:
            for va in valid_artists:
                if isinstance(child, va):
                    artists.append(child)
        return artists, len(artists)

    def _SetColorTooltip(self, artist_id):
        if artist_id in [ARTIST_LINE2D, ARTIST_PATH]:
            self.txt_color.SetToolTip(wx.ToolTip('Please use standard matplotlib colors [b, r, g, y, m, c, k],  #hex colors or grayscale (0-1).'))
        elif artist_id == ARTIST_IMSHOW:
            txt = valid_cmaps.__str__()
            self.txt_color.SetToolTip(wx.ToolTip(txt))


    def get_rgb_from_artist(self, artist, start_color=False):
        segdata = artist.get_cmap()._segmentdata
        if start_color: i = 0
        else: i = 1
        r = segdata['red'][i][1]
        g = segdata['green'][i][1]
        b = segdata['blue'][i][1]
        return (r, g, b)

    def extract_matplotlibcolor_from_rgb(self, rgb):
        '''rgb = (r, g, b)'''
        color = [key for key, value in cv.colors.items() if value == rgb][0]
        return color 

        


    def _SetArtist(self, artist):
        if isinstance(artist, valid_artists[ARTIST_PATH]):
            self._SetColorTooltip(ARTIST_PATH)
            rgb = self.get_rgb_from_artist(artist)
            color = self.extract_matplotlibcolor_from_rgb(rgb)
            self.txt_color.SetValue(color)

        elif isinstance(artist, valid_artists[ARTIST_LINE2D]):
            self.txt_color.SetValue(artist.get_color())
            self.cb_marker.SetValue(artist.get_marker())
            self.cb_artiststyle.SetValue(artist.get_linestyle())
            self._SetColorTooltip(ARTIST_LINE2D)
            self.txt_name.SetValue(artist.get_label())
            
        elif isinstance(artist, valid_artists[ARTIST_IMSHOW]):
            self.txt_color.SetValue(artist.get_cmap().name)
            self.cb_marker.SetValue('')
            self.cb_artiststyle.SetValue('')
            self._SetColorTooltip(ARTIST_IMSHOW)
        else:
            print 'Unknown artist.'




    def _SetAxis(self, ax):

        self.txt_xlabel.SetValue(ax.get_xlabel())
        self.txt_ylabel.SetValue(ax.get_ylabel())
        self.txt_title.SetValue(ax.get_title())
        self.cb_xscale.SetStringSelection(ax.get_xscale())
        self.cb_yscale.SetStringSelection(ax.get_yscale())
        self.txt_xticks.SetValue(ax.get_xticks().__str__())
        self.txt_yticks.SetValue(ax.get_yticks().__str__())
        xlim, ylim = ax.get_xlim(), ax.get_ylim()
        xlim_str, ylim_str = '[ {:.2g}, {:.2g} ]'.format(*xlim), '[ {:.2g}, {:.2g} ]'.format(*ylim)
        self.txt_xlims.SetValue(xlim_str)
        self.txt_ylims.SetValue(ylim_str)

        art, num = self._GetArtists(ax)
        self.cb_artists.Clear()
        if num > 0:
            self._append_artists_to_combobox(art)
            self.SetLine(art[0])
            self.cb_artists.SetValue(self.cb_artists.GetItems()[0])
        else:
            self.SetLine([], blank=True)
            self.cb_artists.SetValue('')

        if self._HasLegend(ax):
            self.btn_legend.SetValue(True)
            self.btn_legend.SetLabel('Remove legend')
        else:
            self.btn_legend.SetValue(False)
            self.btn_legend.SetLabel('Generate legend')

    def _append_artists_to_combobox(self, artists):
        num = len(artists)
        if num > 0:
            for i, item in enumerate(artists):
                if isinstance(item, valid_artists[ARTIST_PATH]):
                    self.cb_artists.Append('PathCollection {}'.format(i))
                elif isinstance(item, valid_artists[ARTIST_IMSHOW]):
                    self.cb_artists.Append('Imshow {}'.format(i))
                else:                    
                    self.cb_artists.Append(item.__str__().split('(')[0]+' ['+item.get_color()+']')
        

    def on_hspan(self, xmin, xmax):
        print xmin, xmax
        self.hspan_sel.deactivate_hspan()
        # self.cid_button_press_event = self.parent.canvas.figure.canvas.mpl_connect('button_press_event', self.mouse_click)
        

    def fit_func(self, event):
        ax = self.GetCurrentAxis()
        # self.parent.canvas.figure.canvas.mpl_disconnect(self.cid_button_press_event)
        # self.hspan_sel = MySpanSelector(ax, self.on_hspan, 'horizontal', rectprops=dict(facecolor='red',alpha=0.3))
        # self.hspan_sel.activate_hspan(self.on_hspan)
        print 'hej'
        self.hspan_sel.visible = True



    def UpdateAxesList(self, fig):
        self.cb_axes.Clear()
        for i, a in enumerate(fig.get_axes()):
            self.cb_axes.Append('Axis ({}, {})'.format(i/a.numCols, i%a.numCols))
        self.cb_axes.SetSelection(0)


    def OnAxes(self, event):
        ax = self.parent.canvas.figure.get_axes()[self.cb_axes.GetSelection()]
        self._SetAxis(ax)

        self.cb_artists.Clear()
        art, num = self._GetArtists(ax)
        if num > 0:
            for item in art:
                self.cb_artists.Append(item.__str__()) 
            self.SetLine(art[0])
            self.cb_artists.SetValue(art.__str__())
        else:
            self.SetLine([], blank=True)
            self.cb_artists.SetValue('')

    


    def SetLine(self, artist, blank=False):
        if not blank:
            self._SetArtist(artist)
        else:
            self.txt_color.SetValue('')
            self.cb_artiststyle.SetStringSelection('')
            self.cb_marker.SetStringSelection('')
        self.cb_artists.SetSelection(0)
            
    def OnArtists(self, event):
        line_nr = self.cb_artists.GetSelection()
        ax_nr = self.cb_axes.GetSelection()
        ax = self.parent.canvas.figure.get_axes()[ax_nr]
        art, num = self._GetArtists(ax)
        artist = art[line_nr]
        self._SetArtist(artist)

    def TightLayout(self, event):
        self.parent.canvas.figure.tight_layout()
        wx.CallAfter(self.parent.canvas.draw)

    def GetCurrentAxis(self):
        return self.parent.canvas.figure.get_axes()[self.cb_axes.GetSelection()]

    def gca(self): return self.GetCurrentAxis()

    def get_current_artist(self, artist_type = ARTIST_LINE2D):
        cur_sel = self.cb_artists.GetSelection()
        ax = self.gca()
        art, num = self._GetArtists(ax)
        cur_art = art[cur_sel] 
        if isinstance(cur_art, valid_artists[artist_type]):
            return cur_art
        else: return None


    def SetLabelLineWidth(self, width):
        ax = self.gca()
        leg = ax.get_legend()
        if not isinstance( leg, type(None) ):
            for line in leg.get_lines():
                line.set_linewidth(width)
            self.parent.canvas.draw()

    def Update(self, event):
        ax = self.parent.canvas.figure.get_axes()[self.cb_axes.GetSelection()]
        ax.set_xscale(self.cb_xscale.GetStringSelection())
        ax.set_yscale(self.cb_yscale.GetStringSelection())
        ax.set_xlabel(self.txt_xlabel.GetValue())
        ax.set_ylabel(self.txt_ylabel.GetValue())
        ax.set_title(self.txt_title.GetValue())

        xticks = self.txt_xticks.GetValue()
        xticks = np.fromstring(xticks[1:-2], dtype=float, sep=' ')
        ax.set_xticks(xticks)

        yticks = self.txt_yticks.GetValue()
        yticks = np.fromstring(yticks[1:-2], dtype=float, sep=' ')
        ax.set_yticks(yticks)

        xlim = self.txt_xlims.GetValue()
        xlim = np.fromstring(xlim[1:-2], dtype=float, sep=', ')
        ax.set_xlim(xlim)

        ylim = self.txt_ylims.GetValue()
        ylim = np.fromstring(ylim[1:-2], dtype=float, sep=',')
        ax.set_ylim(ylim)


        sel = self.cb_artists.GetSelection()
        try:
            artist, num = self._GetArtists(ax)
            artist=artist[sel]
        except IndexError: 
            return

        if isinstance(artist, valid_artists[ARTIST_PATH]):
            col = self.txt_color.GetValue()
            if self.validate_letter_color(col):
                self.set_color_path_collection(ax, artist, col)
            print 'implement this'
        elif isinstance(artist, valid_artists[ARTIST_LINE2D]):
            col = self.txt_color.GetValue()
            if self.ValidateColor(col):
                artist.set_color(col)
            artist.set_linestyle(self.cb_artiststyle.GetValue())
            artist.set_marker(self.cb_marker.GetStringSelection())
            artist.set_label(self.txt_name.GetValue())

        elif isinstance(artist, valid_artists[ARTIST_IMSHOW]):
            cmap = self.txt_color.GetValue()
            if self._ValidColormap(cmap):
                artist.set_cmap(cmap)
        else:
            print 'Not valid artist.'
        wx.CallAfter(self.parent.canvas.draw)





    def set_color_path_collection(self, ax, artist, color):
        if not isinstance(artist, valid_artists[ARTIST_PATH]): return
        x = artist.get_offsets()[:,0] #extract xdata
        y = artist.get_offsets()[:,1] #extract ydata
        current_sel = self.cb_artists.GetSelection()

        color_init=cmaps0[color](int(np.rint(white_level * 255)))
        col = cv.to_rgb(color)
        cmap = colors.LinearSegmentedColormap.from_list('', [color_init, col])
        n_points = np.linspace(0, 1, len(x))
        ax.scatter(x, y, c=n_points, lw=0, cmap=cmap)
        artist.remove()

        #Make the order in the combobox correct again
        cc = ax.collections[:-1]
        cc.insert(current_sel, ax.collections[-1])
        ax.collection = cc

        ax = self.gca()
        art, num = self._GetArtists(ax)
        self.cb_artists.Clear()
        if num > 0:
            self._append_artists_to_combobox(art)
        self.cb_artists.SetSelection(current_sel)
        wx.CallAfter(self.parent.canvas.draw)


    def _ValidColormap(self, cmap):
        if cmap in valid_cmaps: return True
        else: return False

    def validate_letter_color(self, c):
        if c in ['b', 'r', 'g', 'y', 'm', 'c', 'k']:
            return True
        return False

    def ValidateColor(self, c):
        if c.isalpha():
            return self.validate_letter_color(c)
        if re.search(r'^#(?:[0-9a-fA-F]{3}){1,2}$', c): #valid hex code?
            return True
        try:
            if float(c) >= 0 and float(c) <= 1:
                return True
        except ValueError:
            pass
        print 'Color is not valid, see tooltip for valid values.'
        return False




    
        


class ShellPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.shell = Shell(self)
        self.shell.clear()

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.shell, 1, wx.GROW)
        # self.sizer.Add(wx.StaticText(self, -1, 'Linestyle: '), 0)

        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()


class FigurePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        # self.LoadFigure(filepath)
        figure, ax=plt.subplots()
        self.fig_loadsize_inches = figure.get_size_inches()
        self.canvas = FigureCanvas(self, -1, figure)
        self.tb = Toolbar(self.canvas)
        self.tb.Realize()

        self.toolpanel = ToolPanel(self)
        self.shellpanel = ShellPanel(self)

        self.active_xspan = False


        self.s1 = wx.GridBagSizer(hgap=5, vgap=5)
        self.s1.Add(self.canvas, pos=(0,0), flag=wx.GROW)
        self.s1.Add(self.tb, pos=(1,0), flag=wx.GROW)

        bs1 = wx.BoxSizer(wx.VERTICAL)
        bs1.Add(self.s1, 0, wx.GROW)
        bs1.Add(self.shellpanel, 1, wx.GROW)

        s2 = wx.BoxSizer(wx.HORIZONTAL)
        s2.Add(bs1, 1, wx.GROW)
        s2.Add(self.toolpanel, 0, wx.GROW)
        
        self.sizer.Add(s2, 5, wx.GROW)


        self.SetSizer(self.sizer)
        self.Layout()
        self.Fit()

        self.cid_button_press_event = self.canvas.mpl_connect('button_press_event', self.mouse_click)
        self.cid_button_release_event = self.canvas.mpl_connect('button_release_event', self.mouse_release)
        self.cid_button_motion_event = self.canvas.mpl_connect('motion_notify_event', self.mouse_motion)

    def mouse_release(self, event):
        self.active_xspan = False

    def fit_line(self, xmin, xmax):
        cur_art = self.toolpanel.get_current_artist()
        if not cur_art == None:
            if xmin>xmax: xmin, xmax = xmax, xmin
            x, y = cur_art.get_xdata(), cur_art.get_ydata()
            ii = np.logical_and(x > xmin, x < xmax)
            x = x[ii]
            y = y[ii]
            degree = 4
            if len(x) > degree:
                coefs = poly.polyfit(x, y, degree)
                (xmi, xma) = self.toolpanel.gca().get_xlim()
                xfit = np.linspace(xmi, xma, 100)
                yfit = poly.polyval(xfit, coefs)
                ax_sel = self.toolpanel.cb_axes.GetSelection()
                if self.fit_lines[ax_sel] is None:
                    line, = self.toolpanel.gca().plot(xfit, yfit, 'k--')
                    self.fit_lines[ax_sel] = line
                else:
                    self.fit_lines[ax_sel].set_ydata(yfit)

                wx.CallAfter(self.canvas.draw)



    def mouse_motion(self, event):
        if self.active_xspan:
            x = event.xdata
            new_width = x - self.xstart
            self.rect.set_width(new_width)
            self.fit_line(self.xstart, x)
            wx.CallAfter(self.canvas.draw)

    def click_for_xspan(self, event):
        if hasattr(self, 'rect'):
            self.rect.remove()
        self.active_xspan = True
        self.xstart = event.xdata
        ax = self.toolpanel.gca()
        ymin = ax.get_ylim()[0]
        yspan = ax.get_ylim()[1] - ax.get_ylim()[0]
        self.rect = ax.add_patch(Rectangle((event.xdata, ymin), 0, yspan))
        self.rect.set_alpha(0.3)
        self.rect.set_linewidth(0)
        wx.CallAfter(self.canvas.draw)

    def mouse_click(self, event):
        ax = self.toolpanel.gca()
        if not event.inaxes == ax:
            self.click_on_axis(event)
        if event.button == 3:
            self.click_for_xspan(event)
        
    def click_on_axis(self, event):

        for i, ax in enumerate(self.canvas.figure.get_axes()):
            if event.inaxes == ax:
                self.toolpanel._SetAxis(ax)
                self.toolpanel.cb_axes.SetSelection(i)


    def LoadFigure(self, filepath):
        if hasattr(self, 'fit_lines'):
            for line in self.fit_lines: 
                if not line is None: line.remove()
        self.canvas.figure.clf()

        with open(filepath, 'rb') as fil:
            figure = pickle.load(fil)

        self.tb.Destroy()
        self.canvas.Destroy()
        self.canvas = FigureCanvas(self, -1, figure)
        self.tb = Toolbar(self.canvas)
        self.tb.Realize()
        self.s1.Add(self.canvas, pos=(0,0), flag=wx.GROW)
        self.s1.Add(self.tb, pos=(1,0), flag=wx.GROW)
        self.cid_button_press_event = self.canvas.mpl_connect('button_press_event', self.mouse_click)
        self.cid_button_release_event = self.canvas.mpl_connect('button_release_event', self.mouse_release)
        self.cid_button_motion_event = self.canvas.mpl_connect('motion_notify_event', self.mouse_motion)
        self.toolpanel._SetAxis(self.canvas.figure.get_axes()[0])

        self.fit_lines = [None]*len(self.canvas.figure.get_axes())
        self.toolpanel.UpdateAxesList(figure)
        self.toolpanel.UpdateFigureSize(figure)
        cmd = 'fig = frame.panel.canvas.figure'
        frame.panel.shellpanel.shell.run(cmd)

        # self.canvas.draw()
        self.Layout()
        self.Fit()
        self.parent.Fit()




ID_OPEN = 1
ID_SAVE = 2
ID_QUIT = 3

class FigureFrame(wx.Frame):
    def __init__(self, parent, id, title, size):
        wx.Frame.__init__(self, parent, id, title, size=size)

        self.panel = FigurePanel(self)

        self.CreateStatusBar()
        file_menu = wx.Menu()
        item_quit = wx.MenuItem(file_menu, ID_QUIT, '&Quit\tCtrl+Q', 'Quit program')
        file_menu.AppendItem(item_quit)

        item_open = wx.MenuItem(file_menu, ID_OPEN, '&Open...\tCtrl+O', 'Open file')
        file_menu.AppendItem(item_open)

        item_save = wx.MenuItem(file_menu, ID_SAVE, '&Save file\tCtrl+S', 'Save file')
        file_menu.AppendItem(item_save)


        menu_bar = wx.MenuBar()
        menu_bar.Append(file_menu, '&File')
        self.SetMenuBar(menu_bar)

        self.Bind(wx.EVT_MENU, self.OnOpen, id=ID_OPEN)
        self.Bind(wx.EVT_MENU, self.OnSave, id=ID_SAVE)
        self.Bind(wx.EVT_MENU, self.OnQuit, id=ID_QUIT)




    def OnOpen(self, event):
        dlg = wx.FileDialog(self, "Open figure file", "", "",
                                       "Pickle files (*.p;*.pickle)|*.p;*.pickle|All files (*.*)|*.*", wx.FD_OPEN | wx.FD_FILE_MUST_EXIST)

        result = dlg.ShowModal()
        if result == wx.ID_CANCEL:
            return

        path = dlg.GetPath()
        self.panel.LoadFigure(path)
        wx.CallAfter(self.panel.canvas.draw)

    def OnSave(self, event):
        # Fetch the required filename and file type.
        filetypes, exts, filter_index = self.panel.canvas._get_imagesave_wildcards()
        default_file = self.panel.canvas.get_default_filename()
        dlg = wx.FileDialog(self, "Save to file", "", default_file,
                            filetypes,
                            wx.SAVE|wx.OVERWRITE_PROMPT)
        dlg.SetFilterIndex(filter_index)
        if dlg.ShowModal() == wx.ID_OK:
            dirname  = dlg.GetDirectory()
            filename = dlg.GetFilename()
            # DEBUG_MSG('Save file dir:%s name:%s' % (dirname, filename), 3, self)
            format = exts[dlg.GetFilterIndex()]
            basename, ext = os.path.splitext(filename)
            if ext.startswith('.'):
                ext = ext[1:]
            if ext in ('svg', 'pdf', 'ps', 'eps', 'png') and format!=ext:
                #looks like they forgot to set the image type drop
                #down, going with the extension.
                # warnings.warn('extension %s did not match the selected image type %s; going with %s'%(ext, format, ext), stacklevel=0)
                format = ext
            try:
                self.panel.canvas.print_figure(
                    os.path.join(dirname, filename), format=format)
            except Exception as e:
                # error_msg_wx(str(e))
                print e

    def OnQuit(self, event):
        dlg = wx.MessageDialog(self, 'Are you sure you want to quit?', 'Closing', wx.YES_NO | wx.ICON_QUESTION)
        result = dlg.ShowModal()
        if result == wx.ID_YES:
            self.Destroy()

    def gca(self):
        return self.panel.toolpanel.gca()

    def SetLabelLineWidth(self, width):
        self.panel.toolpanel.SetLabelLineWidth(width)



class help(object):
    def __init__(self):
        self.s = r"""
Useful commands:

<ax>.title.set_fontsize(size)
<ax>.yaxis.label.set_fontsize(size)
<ax>.yaxis.label.set_fontsize(size)
for lab in <ax>.get_xticklabels():
    lab.set_fontsize(size)

<object>.set_fontname(font)

<frame>.SetLegendLineWidth(width) // sets the marker width on the legend

"""

    def __repr__(self):
        return self.s


class Getter(object):
    def __init__(self, frame):
        self.frame = frame

    @staticmethod
    @property
    def fig(self):
        return self.frame.panel.canvas.figure

    @staticmethod
    @property
    def gca(self):
        return self.frame.gca()
    
    


def testfigure():
    import string
    import random
    def id_gen(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    fig, ax = plt.subplots(4, 3)
    for a in ax.flatten()[2:]:
        for i in range(4):
            x, y = np.random.random(100), np.random.random(100)
            a.plot(x, y)
        a.set_xlabel(id_gen())
        a.set_ylabel(id_gen())

    data = np.random.random((100, 100))
    ax.flatten()[0].imshow(data)
    ax.flatten()[3].set_xscale('log')
    ax.flatten()[3].set_yscale('log')
    ax.flatten()[4].set_xscale('log')
    with open('test4.p', 'wb') as fil:
        pickle.dump(fig, fil)

def testfigure2():
    import string
    import random
    def id_gen(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for _ in range(size))

    fig, ax = plt.subplots(2, 1)
    for a in ax.flatten():
        for i in range(4):
            x = np.linspace(-10, 10, 100)
            y = x**i
            a.plot(x, y)
        a.set_xlabel(id_gen())
        a.set_ylabel(id_gen())

    with open('test5.p', 'wb') as fil:
        pickle.dump(fig, fil)



HELP = help()


if __name__ == "__main__":
    import sys
    if 'test' in sys.argv:
        testfigure2()
    app = wx.App(False)
    frame = FigureFrame(None, -1, title='Figure Loader', size=(wx.DisplaySize()[0]/2, wx.DisplaySize()[1]*3/4))
    get = Getter(frame)
    frame.panel.shellpanel.shell.write(
    '''
    Welcome to the figure customisation tool
    ========================================

    Type HELP to access some useful commands.

    ''')
    cmd = ['fig = frame.panel.canvas.figure']
    for c in cmd:
        frame.panel.shellpanel.shell.run(c)
    frame.Show()
    try:
        if os.environ['COMPUTERNAME'] == 'OBIWAN':
            frame.panel.LoadFigure('test5.p')
            wx.CallAfter(frame.panel.canvas.draw)
    except KeyError:
        pass
    app.MainLoop()