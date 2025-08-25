<script lang="ts">
	import { chatState, chatActions, activeConversation } from '$stores/chat';
	import { formatDate } from '$lib/utils';
	import Button from '../ui/button.svelte';
	import { MessageSquare, Trash2, Edit } from 'lucide-svelte';
	import { cn } from '$lib/utils';

	let editingId = $state<string | null>(null);
	let editTitle = $state('');

	function selectConversation(id: string) {
		chatActions.selectConversation(id);
	}

	function startEdit(conversation: any) {
		editingId = conversation.id;
		editTitle = conversation.title;
	}

	function saveEdit() {
		if (editingId && editTitle.trim()) {
			chatActions.updateConversationTitle(editingId, editTitle.trim());
		}
		editingId = null;
		editTitle = '';
	}

	function cancelEdit() {
		editingId = null;
		editTitle = '';
	}

	function deleteConversation(id: string, event: Event) {
		event.preventDefault();
		event.stopPropagation();
		
		if (confirm('Are you sure you want to delete this conversation?')) {
			chatActions.deleteConversation(id);
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter') {
			saveEdit();
		} else if (event.key === 'Escape') {
			cancelEdit();
		}
	}
</script>

<div class="flex-1 overflow-auto custom-scrollbar">
	<div class="p-2 space-y-1">
		{#each $chatState.conversations as conversation (conversation.id)}
			<div
				class={cn(
					'group relative rounded-lg p-3 cursor-pointer transition-colors',
					$activeConversation?.id === conversation.id 
						? 'bg-accent text-accent-foreground' 
						: 'hover:bg-muted'
				)}
				role="button"
				tabindex="0"
				onclick={() => selectConversation(conversation.id)}
				onkeydown={(e) => e.key === 'Enter' && selectConversation(conversation.id)}
			>
				<div class="flex items-start justify-between">
					<div class="flex-1 min-w-0">
						{#if editingId === conversation.id}
							<input
								type="text"
								bind:value={editTitle}
								onkeydown={handleKeydown}
								onblur={saveEdit}
								class="w-full bg-background border border-border rounded px-2 py-1 text-sm"
								autofocus
							/>
						{:else}
							<div class="flex items-center space-x-2">
								<MessageSquare class="h-3 w-3 flex-shrink-0 text-muted-foreground" />
								<h3 class="font-medium text-sm truncate">
									{conversation.title}
								</h3>
							</div>
							<p class="text-xs text-muted-foreground mt-1">
								{formatDate(conversation.updatedAt)}
							</p>
							{#if conversation.messages.length > 0}
								<p class="text-xs text-muted-foreground truncate mt-1">
									{conversation.messages[conversation.messages.length - 1]?.content.slice(0, 50)}...
								</p>
							{/if}
						{/if}
					</div>
					
					{#if editingId !== conversation.id}
						<div class="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
							<Button
								size="icon"
								variant="ghost"
								class="h-6 w-6"
								onclick={(e) => {
									e.stopPropagation();
									startEdit(conversation);
								}}
								title="Rename"
							>
								<Edit class="h-3 w-3" />
							</Button>
							<Button
								size="icon"
								variant="ghost"
								class="h-6 w-6 text-destructive hover:text-destructive"
								onclick={(e) => deleteConversation(conversation.id, e)}
								title="Delete"
							>
								<Trash2 class="h-3 w-3" />
							</Button>
						</div>
					{/if}
				</div>
			</div>
		{:else}
			<div class="text-center py-8">
				<MessageSquare class="h-8 w-8 text-muted-foreground mx-auto mb-2" />
				<p class="text-sm text-muted-foreground">No conversations yet</p>
				<p class="text-xs text-muted-foreground mt-1">Start a new chat to get began</p>
			</div>
		{/each}
	</div>
</div>