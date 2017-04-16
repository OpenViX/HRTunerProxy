PLUGIN = PlexDVRAPI
CATEGORY ?= "SystemPlugins"

plugindir = $(libdir)/enigma2/python/Plugins/$(CATEGORY)/$(PLUGIN)

LANGS = ar bg ca cs da de el en en_GB es et fa fi fr fy he hr hu is it lt lv nl no nb pl pt pt_BR ro ru sv sk sl sr th tr uk
LANGMO = $(LANGS:=.mo)
LANGPO = $(LANGS:=.po)

# the TRANSLATORS: allows putting translation comments before the to-be-translated line.
$(PLUGIN)-py.pot: $(srcdir)/../src/*.py
	$(XGETTEXT) --no-wrap -L Python --from-code=UTF-8 -kpgettext:1c,2 --add-comments="TRANSLATORS:" -d $(PLUGIN) -s -o $@ $^

$(PLUGIN).pot: $(PLUGIN)-py.pot
	sed --in-place $(PLUGIN)-py.pot --expression=s/CHARSET/UTF-8/
	$(MSGUNIQ) --no-wrap --no-location $^ -o $@

%.po: $(PLUGIN).pot
	if [ -f $@ ]; then \
		$(MSGMERGE) --backup=none --no-wrap --no-location -s -N -U $@ $< && touch $@; \
	else \
		$(MSGINIT) -l $@ -o $@ -i $< --no-translator; \
	fi

.po.mo:
	$(MSGFMT) -o $@ $<

BUILT_SOURCES = $(LANGMO)
CLEANFILES = $(LANGMO) $(PLUGIN)-py.pot $(PLUGIN)-xml.pot $(PLUGIN).pot

dist-hook: $(LANGPO)

install-data-local: $(LANGMO)
	for lang in $(LANGS); do \
		$(mkinstalldirs) $(DESTDIR)$(plugindir)/locale/$$lang/LC_MESSAGES; \
		$(INSTALL_DATA) $$lang.mo $(DESTDIR)$(plugindir)/locale/$$lang/LC_MESSAGES/$(PLUGIN).mo; \
		$(INSTALL_DATA) $$lang.po $(DESTDIR)$(plugindir)/locale/$$lang.po; \
	done

uninstall-local:
	for lang in $(LANGS); do \
		$(RM) $(DESTDIR)$(plugindir)/locale/$$lang/LC_MESSAGES/$(PLUGIN).mo; \
	done
