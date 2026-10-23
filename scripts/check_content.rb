#!/usr/bin/env ruby
# Metadata checks only; this does not replace a Jekyll build or link review.
require 'yaml'
require 'date'
require 'pathname'

ROOT = File.expand_path('..', __dir__)
Dir.chdir(ROOT)
errors = []
load_yaml = lambda do |raw, path|
  begin
    result = YAML.safe_load(raw, permitted_classes: [Date, Time], aliases: false)
    raise 'expected a YAML mapping' unless result.is_a?(Hash)
    result
  rescue StandardError => e
    errors << "#{path}: #{e.message}"
    {}
  end
end
config = load_yaml.call(File.read('_config.yml'), '_config.yml')
collections = config.fetch('collections', {})
collections = collections.each_with_object({}) { |name, map| map[name] = {} } if collections.is_a?(Array)
unless collections.is_a?(Hash)
  abort 'Invalid collections configuration: expected a mapping or list.'
end
excluded = %w[README.md AGENTS.md docs scripts tools _templates _site vendor work] + Array(config['exclude'])
files = Dir.glob('**/*.md').reject do |path|
  excluded.any? { |prefix| path == prefix || path.start_with?(prefix.to_s.sub(%r{/$}, '') + '/') }
end
selected = ARGV.empty? ? files : ARGV.map { |p| Pathname.new(p).cleanpath.to_s }
(selected - files).each { |p| errors << "#{p}: not a website Markdown file in this checkout" }
metadata = {}
bodies = {}
files.each do |path|
  text = File.read(path)
  if text.start_with?("---\n", "---\r\n")
    match = text.match(/\A---\r?\n(.*?)\r?\n---\s*\r?\n?(.*)\z/m)
    if match
      metadata[path] = load_yaml.call(match[1], path)
      bodies[path] = match[2]
    else
      errors << "#{path}: unclosed front matter"
      metadata[path] = {}
    end
  else
    metadata[path] = {}
    bodies[path] = text
  end
end
urls = {}
metadata.each do |path, meta|
  next if meta['published'] == false
  url = meta['permalink']
  next unless url
  if !url.is_a?(String) || !url.start_with?('/')
    errors << "#{path}: permalink must be a site-relative path starting with /"
    next
  end
  normalized = url.sub(%r{/index\.html$}, '/').sub(%r{/$}, '')
  errors << "#{path}: duplicate permalink #{url} (also #{urls[normalized]})" if urls[normalized]
  urls[normalized] = path
end
selected.each do |path|
  next unless metadata.key?(path)
  meta = metadata[path]
  next if meta['published'] == false
  collection = collections.keys.find { |name| path.start_with?("_#{name}/") }
  entry = collection || path.start_with?('writing/', 'projects/')
  if entry
    errors << "#{path}: title is required" unless meta['title'].is_a?(String) && !meta['title'].strip.empty?
    date = meta['date']
    valid_date = date.is_a?(Date) || date.is_a?(Time)
    if date.is_a?(String) && date.match?(/\A\d{4}-\d{2}-\d{2}\z/)
      begin
        Date.iso8601(date)
        valid_date = true
      rescue ArgumentError
      end
    end
    errors << "#{path}: date must be a valid YYYY-MM-DD publication date" unless valid_date
    errors << "#{path}: content body is empty" if bodies.fetch(path, '').strip.empty?
    errors << "#{path}: template placeholders remain" if File.read(path).match?(/REPLACE_[A-Z_]+|YYYY-MM-DD/)
  end
  if meta.key?('tags') && (!meta['tags'].is_a?(Array) || !meta['tags'].all? { |t| t.is_a?(String) })
    errors << "#{path}: tags must be a YAML list of text labels"
  end
  type = collection || 'pages'
  defaults = {}
  Array(config['defaults']).each do |rule|
    scope = rule.fetch('scope', {})
    prefix = scope.fetch('path', '')
    if (scope['type'].nil? || scope['type'] == type) && (prefix.empty? || path == prefix || path.start_with?(prefix + '/'))
      defaults.merge!(rule.fetch('values', {}))
    end
  end
  layout = meta.key?('layout') ? meta['layout'] : defaults['layout']
  if layout && !%w[none null].include?(layout.to_s) && !File.file?("_layouts/#{layout}.html")
    errors << "#{path}: local layout #{layout.inspect} not found; verify any intentional theme-provided layout"
  end
  if collection && collections[collection].is_a?(Hash) && collections[collection]['output'] != true
    errors << "#{path}: collection #{collection} is not configured with output: true"
  end
end
unless errors.empty?
  warn errors.join("\n")
  exit 1
end
puts "Content checks passed (#{selected.size} Markdown files checked; #{metadata.size} scanned for duplicate explicit URLs)."
puts 'This checks metadata, not a full Jekyll build or external links.'
